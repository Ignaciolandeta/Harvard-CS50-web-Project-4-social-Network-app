from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.core.paginator import Paginator
from django.core import serializers

from .models import User, Post, Profile
from .forms import PostForm


import json

# The 'index' view returns index.html template
def index(request):
    #POST valid form
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.cleaned_data['post']
            new_post = Post(user=request.user, post=post)
            new_post.save()
            return HttpResponseRedirect(reverse('index'))

    # Order posts by reverse-cronologicaly. 
    # Pagination: On any page that displays posts, if there are more than max posts, 
    # a “Next” button should appear to take the user to the next page of posts 
    # (which should be older than the current page of posts). 
    # If not on the first page, a “Previous” button should appear to take the user to the previous page of posts as well.-->
    else:
        form = PostForm()
        posts_queryset = Post.objects.order_by('date_added').reverse()

        posts_to_display = Paginator(posts_queryset, 10)
        posts = posts_to_display.page(1)
        if request.GET.get('page'):
            page = int(request.GET.get('page'))
            posts = posts_to_display.page(page)
    
    # Return index.html
    return render(request, "network/index.html", {'form': form, 'posts': posts})


# The 'login_view' view renders a login form when a user tries to GET the page. 
# When a user submits the form using the POST request method, the user is authenticated, 
# logged in, and redirected to the index page.
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
            return render(request, "network/login.html", {
                "message": "Invalid username and/or password, please try again."
            })
    else:
        return render(request, "network/login.html")

# The 'logout_view' view logs the user out and redirects them to the index page.
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))

# The 'register' route displays a registration form to the user, and creates a new user when the form is submitted. 
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "network/register.html", {
                "message": "Hey! Passwords must match, please register."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "network/register.html", {
                "message": "sorry, Username already taken. Try another"
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "network/register.html")


# Profile Page: Clicking on a username should load that user’s profile page. This page should:
# Display the number of followers the user has, as well as the number of people that the user follows.
# Display all of the posts for that user, in reverse chronological order.
# For any other user who is signed in, this page should also display a “Follow” or “Unfollow” button 
# that will let the current user toggle whether or not they are following this user’s posts. 
# Note that this only applies to any “other” user: a user should not be able to follow themselves
def profile(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        btn_value = data['btn_value']
        user_id = data['user_id']
        user = User.objects.get(id=user_id)
        if btn_value == 'unfollow':
            Profile.objects.filter(follower=request.user, following=user).delete()
        else:
            new_profile = Profile(follower=request.user, following=user)
            new_profile.save()
        # confirmation pop-up
        return JsonResponse(f'{btn_value}ed {user} confirmed ', safe=False)
    else:
        user = request.user
        
        # Number of followers the user has, as well as the number of people that the user follows.
        following = Profile.objects.filter(follower=user).count()
        follower = Profile.objects.filter(following=user).count()
        follower_list = [person.following for person in Profile.objects.filter(follower=user)]
        
        # all of the posts for that user, in reverse chronological order, return 'profile.html'
        posts = Post.objects.order_by('date_added').reverse()
        context = {'follower': follower, 'following': following, 'posts': posts, 'follower_list': follower_list}
        return render(request, "network/profile.html", context)



# Following: The “Following” link in the navigation bar should take the user 
# to a page where they see all posts made by users that the current user follows.
# This page should behave just as the “All Posts” page does, just with a more limited set of posts.
# This page should only be available to users who are signed in.

def following(request):
    user_following = []  # all users that the current loged-in user follows (objects list)
    user_following_profile = request.user.following.all() # define a set of all following users
    
    for user in user_following_profile:  # object iteration of user following
        user_following.append(user.following)

    posts = []

    for user in user_following: # see all posts made by users that the current user follows
        posts.extend(Post.objects.filter(user=user).order_by('date_added').reverse())
    
    # The “Following” link in the navigation bar should take the user to following.html page
    return render(request, "network/following.html", {'posts': posts})

# Edit Post: Users should be able to click an “Edit” button or link on any of their own posts to edit that post.
# When a user clicks “Edit” for one of their own posts, the content of their post should be replaced 
# with a textarea where the user can edit the content of their post.
# The user should then be able to “Save” the edited post. 
# Using JavaScript, should be able to achieve this without requiring a reload of the entire page.
# For security, ensure that the application is designed such that it is not possible for a user, 
# via any route, to edit another user’s posts.

def edit(request, post_id):
    post = Post.objects.get(id=post_id)
    if request.method != 'POST':
        # textarea where the user can edit the content of their post
        form = PostForm(initial={'post': post.post})
        return render(request, 'network/edit.html', {'form': form})
    else:
        form = PostForm(request.POST)
        if form.is_valid():
            post.post = form.cleaned_data['post']
            post.save()
        return HttpResponseRedirect(reverse('index'))


# “Like” and “Unlike”: Users should be able to click a button or link on any post to toggle whether or not 
# they “like” that post.
# Using JavaScript, the app should asynchronously let the server know to update the like count 
# (as via a call to fetch) and then update the post’s like count displayed on the page, 
# without requiring a reload of the entire page.

def like(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        post_id = data['post_id']
        heart = data['heart']
        post = Post.objects.get(id=post_id) 

        if 'red' in heart: # if the like emoji is Red and user press it, it will unlike the post
            post.liked_users.remove(request.user)
        else:
            post.liked_users.add(request.user)
        return JsonResponse({'likes': post.liked_users.count(), 'post_id': post_id})
