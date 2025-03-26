from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    owned_decks = models.ManyToManyField('Deck', related_name='owned', blank=True)
    added_decks = models.ManyToManyField('Deck', related_name='added_by_users', blank=True)
    daily_card_limit = models.PositiveIntegerField(default=20)
    #stats
    cards_studied = models.PositiveIntegerField(default=0)
    study_streak = models.PositiveIntegerField(default=0)
    #last_study_date = models.DateField(null=True, blank=True)
    
class Card(models.Model):
    # Changed related_name to avoid conflict
    deck = models.ForeignKey("Deck", on_delete=models.CASCADE, related_name="deck_cards")
    front = models.TextField()
    back = models.TextField()
    reversible = models.BooleanField(default=False)
    ease_history = models.JSONField(default=list)  
    inception = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=10, default="learning")
    siblings = models.ManyToManyField("self", blank=True)
    review_date = models.DateTimeField(auto_now_add=True)  

    def __str__(self):
        return f"Front: {self.front}\nBack: {self.back}\n"

class Deck(models.Model):
    title = models.CharField(max_length=50, default="New Deck")
    description = models.CharField(max_length=250, default="New Deck")
    # This ManyToManyField might be redundant if you're using the ForeignKey in Card
    # You could either remove this or keep it with a different name
    cards = models.ManyToManyField(Card, related_name="decks", blank=True)  
    reviews = models.JSONField(default=list)  
    button_history = models.JSONField(default=list)  
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="owner_of_decks")
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"Title: {self.title}\nNumber of Cards: {self.cards.count()}"