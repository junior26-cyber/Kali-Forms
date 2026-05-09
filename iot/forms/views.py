from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth import login, update_session_auth_hash, authenticate
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django import forms
from django.contrib.auth.decorators import login_required
from .models import Sondage, Question, Option, Response, Answer

# Formulaire de connexion personnalisé avec email
class CustomLoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput, label='Mot de passe')

# Formulaire d'inscription personnalisé avec email
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)  # Ajouter le champ email

    class Meta:
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
        return user

# Page d'accueil
def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'forms/home.html')

@login_required
def dashboard(request):
    sondages = Sondage.objects.filter(creator=request.user).order_by('-created_at')
    return render(request, 'forms/dashboard.html', {'sondages': sondages})

@login_required
def sondage_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        if title:
            sondage = Sondage.objects.create(
                title=title,
                description=description,
                creator=request.user
            )
            return redirect('sondage_builder', sondage_id=sondage.id)
    return render(request, 'forms/sondage_form.html')

@login_required
def sondage_edit(request, sondage_id):
    sondage = get_object_or_404(Sondage, id=sondage_id, creator=request.user)
    if request.method == 'POST':
        sondage.title = request.POST.get('title')
        sondage.description = request.POST.get('description')
        sondage.save()
        return redirect('dashboard')
    return render(request, 'forms/sondage_form.html', {'sondage': sondage})

@login_required
def sondage_delete(request, sondage_id):
    sondage = get_object_or_404(Sondage, id=sondage_id, creator=request.user)
    if request.method == 'POST':
        sondage.delete()
        return redirect('dashboard')
    return render(request, 'forms/sondage_confirm_delete.html', {'sondage': sondage})

@login_required
def sondage_builder(request, sondage_id):
    sondage = get_object_or_404(Sondage, id=sondage_id, creator=request.user)
    questions = sondage.questions.all().prefetch_related('options')
    return render(request, 'forms/sondage_builder.html', {
        'sondage': sondage,
        'questions': questions,
        'question_types': Question.QUESTION_TYPES
    })

@login_required
def question_add(request, sondage_id):
    sondage = get_object_or_404(Sondage, id=sondage_id, creator=request.user)
    if request.method == 'POST':
        text = request.POST.get('text', 'Nouvelle question')
        q_type = request.POST.get('type', 'text')
        is_required = request.POST.get('is_required') == 'on'
        
        # Calculate order
        last_order = sondage.questions.order_by('order').last()
        order = (last_order.order + 1) if last_order else 0
        
        question = Question.objects.create(
            survey=sondage,
            text=text,
            type=q_type,
            is_required=is_required,
            order=order
        )
        
        # Add default options for choice types if needed
        if q_type in ['radio', 'checkbox', 'select']:
            Option.objects.create(question=question, text="Option 1")
        elif q_type == 'boolean':
            Option.objects.create(question=question, text="Oui")
            Option.objects.create(question=question, text="Non")
            
        return redirect('sondage_builder', sondage_id=sondage.id)
    return redirect('sondage_builder', sondage_id=sondage.id)

@login_required
def question_edit(request, question_id):
    question = get_object_or_404(Question, id=question_id, survey__creator=request.user)
    if request.method == 'POST':
        question.text = request.POST.get('text')
        question.type = request.POST.get('type')
        question.is_required = request.POST.get('is_required') == 'on'
        question.save()
        
        # Handle options for choice types
        if question.type in ['radio', 'checkbox', 'select']:
            option_ids = request.POST.getlist('option_ids')
            option_texts = request.POST.getlist('option_texts')
            
            # Update existing options
            for oid, otext in zip(option_ids, option_texts):
                if oid:
                    opt = Option.objects.get(id=oid, question=question)
                    opt.text = otext
                    opt.save()
            
            # Add new options
            new_options = request.POST.getlist('new_option_texts')
            for otext in new_options:
                if otext.strip():
                    Option.objects.create(question=question, text=otext)
        
        return redirect('sondage_builder', sondage_id=question.survey.id)
    return redirect('sondage_builder', sondage_id=question.survey.id)

@login_required
def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id, survey__creator=request.user)
    sondage_id = question.survey.id
    if request.method == 'POST':
        question.delete()
    return redirect('sondage_builder', sondage_id=sondage_id)

@login_required
def option_delete(request, option_id):
    option = get_object_or_404(Option, id=option_id, question__survey__creator=request.user)
    sondage_id = option.question.survey.id
    option.delete()
    return redirect('sondage_builder', sondage_id=sondage_id)

# Vues publiques pour répondre au sondage
def sondage_view(request, sondage_id):
    sondage = get_object_or_404(Sondage, id=sondage_id, is_active=True)
    questions = sondage.questions.all().prefetch_related('options')
    return render(request, 'forms/sondage_view.html', {
        'sondage': sondage,
        'questions': questions
    })

def sondage_submit(request, sondage_id):
    sondage = get_object_or_404(Sondage, id=sondage_id, is_active=True)
    if request.method == 'POST':
        response = Response.objects.create(
            survey=sondage,
            user=request.user if request.user.is_authenticated else None
        )
        
        for question in sondage.questions.all():
            answer = Answer.objects.create(response=response, question=question)
            
            if question.type in ['text', 'textarea']:
                answer.text_value = request.POST.get(f'q_{question.id}')
            elif question.type == 'radio' or question.type == 'select' or question.type == 'boolean':
                option_id = request.POST.get(f'q_{question.id}')
                if option_id:
                    option = get_object_or_404(Option, id=option_id, question=question)
                    answer.selected_options.add(option)
            elif question.type == 'checkbox':
                option_ids = request.POST.getlist(f'q_{question.id}')
                for oid in option_ids:
                    option = get_object_or_404(Option, id=oid, question=question)
                    answer.selected_options.add(option)
            
            answer.save()
            
        return render(request, 'forms/sondage_thanks.html', {'sondage': sondage})
    return redirect('sondage_view', sondage_id=sondage_id)

@login_required
def sondage_results(request, sondage_id):
    sondage = get_object_or_404(Sondage, id=sondage_id, creator=request.user)
    responses = sondage.responses.all().order_by('-created_at')
    responses_count = responses.count()
    
    questions = sondage.questions.all()
    questions_data = []
    
    # Statistiques par question
    for question in questions:
        data = {'question': question, 'answers_list': []}
        
        if question.type in ['text', 'textarea']:
            # Récupérer les 20 dernières réponses textuelles non vides
            data['answers_list'] = Answer.objects.filter(
                question=question, 
                response__survey=sondage
            ).exclude(text_value='').values_list('text_value', flat=True)[:20]
        else:
            options_stats = []
            for option in question.options.all():
                count = Answer.objects.filter(
                    question=question, 
                    selected_options=option,
                    response__survey=sondage
                ).count()
                options_stats.append({
                    'text': option.text,
                    'count': count,
                    'percentage': (count / responses_count * 100) if responses_count > 0 else 0
                })
            data['options_stats'] = options_stats
            
        questions_data.append(data)
    
    # Tableau détaillé des réponses
    table_headers = [q.text for q in questions]
    table_rows = []
    for resp in responses:
        row = {'id': resp.id, 'date': resp.created_at, 'answers': []}
        for q in questions:
            ans = Answer.objects.filter(response=resp, question=q).first()
            if ans:
                if q.type in ['text', 'textarea']:
                    row['answers'].append(ans.text_value or '-')
                else:
                    opts = ", ".join([o.text for o in ans.selected_options.all()])
                    row['answers'].append(opts or '-')
            else:
                row['answers'].append('-')
        table_rows.append(row)
        
    return render(request, 'forms/sondage_results.html', {
        'sondage': sondage,
        'responses_count': responses_count,
        'questions_data': questions_data,
        'table_headers': table_headers,
        'table_rows': table_rows
    })

# Vue de connexion personnalisée
def custom_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            try:
                user_obj = User.objects.get(email=email)  # Trouver l'utilisateur par email
                user = authenticate(request, username=user_obj.username, password=password)  # Authentifier avec username
                if user is not None:
                    login(request, user)
                    return redirect('home')
                else:
                    form.add_error(None, 'Mot de passe incorrect.')
            except User.DoesNotExist:
                form.add_error(None, 'Email non trouvé.')
    else:
        form = CustomLoginForm()
    return render(request, 'forms/login.html', {'form': form})

# Vue d'inscription
def signup(request):
    if request.method == 'POST':  # Si le formulaire est soumis
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():  # Si le formulaire est valide
            user = form.save()  # Sauvegarder le nouvel utilisateur
            login(request, user)  # Connecter l'utilisateur
            return redirect('home')  # Rediriger vers l'accueil
    else:
        form = CustomUserCreationForm()  # Formulaire vide
    return render(request, 'forms/signup.html', {'form': form})

# Vue de déconnexion
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')  # Rediriger vers l'accueil après déconnexion

# Vue pour mot de passe oublié (avec username)
def forgot_password(request):
    user = None
    if request.method == 'POST':
        if 'username' in request.POST:  # Étape 1 : saisir le username
            username = request.POST.get('username')
            try:
                user = User.objects.get(username=username)  # Chercher l'utilisateur par username
            except User.DoesNotExist:
                user = None
        elif 'new_password1' in request.POST and request.session.get('reset_user_id'):  # Étape 2 : nouveau mot de passe
            user_id = request.session['reset_user_id']
            user = User.objects.get(id=user_id)
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()  # Sauvegarder le nouveau mot de passe
                update_session_auth_hash(request, user)
                request.session.pop('reset_user_id', None)  # Nettoyer la session
                return redirect('home')  # Rediriger vers l'accueil
            else:
                return render(request, 'forms/forgot_password.html', {'user': user, 'form': form})
    if user:
        request.session['reset_user_id'] = user.id  # Stocker l'ID en session
        form = SetPasswordForm(user)
        return render(request, 'forms/forgot_password.html', {'user': user, 'form': form})
    else:
        return render(request, 'forms/forgot_password.html', {'user': None})
