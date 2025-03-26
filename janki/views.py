from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.db import IntegrityError
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import User, Card, Deck
import json
from datetime import timedelta

# Create your views here.
def index(request):
    return render(request, "janki/index.html", {
        "user": request.user
    })

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "janki/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "janki/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "janki/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "janki/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "janki/register.html")


def stats(request): 
    return render(request, "janki/stats.html")

def profile_view(request, username):
    # Get the user profile
    try:
        user_profile = User.objects.get(username=username)
    except User.DoesNotExist:
        # Handle case where user doesn't exist
        return render(request, "janki/error.html", {
            "message": "User not found."
        })
    
    # Add any other profile-related data you want to show
    
    return render(request, "janki/profile.html", {
        "profile_user": user_profile,
    })

@login_required
def create_deck(request):
    if request.method == "POST":
        title = request.POST.get("title", "New Deck")
        description = request.POST.get("description", "")
        
        # Create a new deck with the current user as owner
        deck = Deck(
            title=title,
            description=description,
            owner=request.user
        )
        deck.save()
        
        # Add this deck to the user's added_decks
        request.user.added_decks.add(deck)
        
        # Redirect to the newly created deck
        return HttpResponseRedirect(reverse("view_deck", args=[deck.id]))
    
    return render(request, "janki/create_deck.html")

@login_required
def view_deck(request, deck_id):
    try: 
        deck = Deck.objects.get(id=deck_id)
        review_complete = request.GET.get('review_complete') == '1'
        
        return render(request, "janki/view_deck.html", {
            "deck": deck,
            "review_complete": review_complete
        })
    except Deck.DoesNotExist:
        error_view(request, "deck not found")
    
def error_view(request, message):
    return render(request, "janki/error.html")

# Edit an existing deck
@login_required
def edit_deck(request, deck_id):
    deck = Deck.objects.get(id=deck_id)

    # Handle form submission
    if request.method == "POST":
        title = request.POST.get("title")
        description = request.POST.get("description")
        
        # Update the deck
        if title:
            deck.title = title
        if description:
            deck.description = description
        deck.save()
        
        # Redirect to the deck view
        return HttpResponseRedirect(reverse("view_deck", args=[deck.id]))
    
    # GET request - display the form
    return render(request, "janki/edit_deck.html", {
        "deck": deck
    })
        
@login_required
def add_card(request):
    selected_deck = None
    
    # Check if there's a deck_id in the GET parameters
    deck_id = request.GET.get('deck_id')
    if deck_id:
        try:
            deck = Deck.objects.get(id=deck_id)
            if deck.owner == request.user or request.user in deck.added_by_users.all():
                selected_deck = deck.title
        except Deck.DoesNotExist:
            pass
    
    if request.method == "POST":
        # Process the form submission
        deck_title = request.POST.get("choose_deck")
        front = request.POST.get("front")
        back = request.POST.get("back")
        reversible = request.POST.get("reversible") == "yes" 
        
        # Debug - print the values
        print(f"POST data: {request.POST}")
        print(f"Deck: {deck_title}, Front: {front}, Back: {back}, Reversible: {reversible}")
        
        if not front or not back:
            return render(request, "janki/add_card.html", {
                "selected_deck": selected_deck,
                "message": "Front and back content is required."
            })
        
        try:
            deck = Deck.objects.get(title=deck_title)
            
            # Create a new card 
            card = Card(
                deck=deck,
                front=front,
                back=back,
                reversible=reversible
            )

            card.save()
            deck.cards.add(card)
            deck.save()

            # Redirect to cleared add card view
            return render(request, "janki/add_card.html", {
                "selected_deck": deck_title,
                "message": "Front and back content is required."
            })
        
        except Deck.DoesNotExist:
            return render(request, "janki/error.html", {
                "message": "Deck not found."
            })
    
    return render(request, "janki/add_card.html", {
        "selected_deck": selected_deck
    })

# Get the next due card in a deck
def get_next_card(deck):
    complete = False
    card = None

    # Get due cards - use deck_cards instead of cards
    current_time = timezone.now()
    due_cards = deck.deck_cards.filter(review_date__lte=current_time).order_by('review_date')

    # Finish if no due cards
    if not due_cards.exists():
            complete = True
            return complete, card

    # Otherwise return first card and details
    card = due_cards.first()
    return complete, card


def process_review(request):
    data = json.loads(request.body)
    card_id = data.get('card_id')
    difficulty = int(data.get('difficulty'))  # Convert to integer

    try:
        card = Card.objects.get(id=card_id)
        
        # Update card based on difficulty
        now = timezone.now()
        
        # Simple spaced repetition algorithm
        if difficulty == 1:  # Again
            interval = timedelta(minutes=1)
        elif difficulty == 2:  # Hard
            interval = timedelta(days=1)
        elif difficulty == 3:  # Good
            interval = timedelta(days=3)
        elif difficulty == 4:  # Easy
            interval = timedelta(days=7)
        else:
            # Default case if difficulty is not 1-4
            interval = timedelta(days=1)
        
        # Update card
        card.review_date = now + interval
        
        # Update state if needed
        if card.state == "learning" and difficulty >= 3:
            card.state = "review"
            
        # Save ease history
        ease_history = card.ease_history
        ease_history.append(difficulty)
        card.ease_history = ease_history
        card.save()
        
        # Check if there are more cards
        deck = card.deck
        complete, next_card = get_next_card(deck)
        
        response_data = {
            "success": True,
            "complete": complete
        }
        
        if not complete:
            response_data["next_card"] = {
                "id": next_card.id,
                "front": next_card.front,
                "back": next_card.back,
                "reversible": next_card.reversible
            }
            
        return JsonResponse(response_data)
        
    except Card.DoesNotExist:
        return JsonResponse({"success": False, "error": "Card not found"}, status=404)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)  


@login_required
def review_deck(request, deck_id):
    try:
        deck = Deck.objects.get(id=deck_id)
        complete, card = get_next_card(deck)
        
        if complete:
            # Redirect to view_deck with completion flag
            return HttpResponseRedirect(f"{reverse('view_deck', args=[deck_id])}?review_complete=1")
            
        return render(request, "janki/review.html", {
            "deck": deck,
            "card": card,
            "complete": complete
        })
    except Deck.DoesNotExist:
        return error_view(request, "Deck not found")
