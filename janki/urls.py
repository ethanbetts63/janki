from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("stats/", views.stats, name="stats"), 
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("profile/<str:username>", views.profile_view, name="profile"),
    path('add_card/', views.add_card, name='add_card'),
    path("deck/create/", views.create_deck, name="create_deck"),
    path("deck/<int:deck_id>/edit/", views.edit_deck, name="edit_deck"),
    path("deck/<int:deck_id>/", views.view_deck, name="view_deck"),
    path("deck/<int:deck_id>/review/", views.review_deck, name="review_deck"),
    path('process_review/', views.process_review, name='process_review'),
    path("error", views.error_view, name="error")
]
