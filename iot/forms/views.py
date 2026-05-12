from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.forms import UserCreationForm, SetPasswordForm
from django.contrib.auth import login, update_session_auth_hash, authenticate
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django import forms
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Sondage, Question, Option, Response, Answer

# Formulaire de connexion personnalisé avec email
class CustomLoginForm(forms.Form):
    email = forms.EmailField(label='Email')
    password = forms.CharField(widget=forms.PasswordInput, label='Mot de passe')

# Formulaire d'inscription personnalisé avec email unique
class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')

    class Meta:
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Cette adresse email est déjà associée à un compte.")
        return email

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
    try:
        sondage = Sondage.objects.get(id=sondage_id, creator=request.user)
    except Sondage.DoesNotExist:
        messages.error(request, "Accès refusé : vous n'êtes pas le propriétaire de ce sondage.")
        return redirect('dashboard')
        
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
            sondage=sondage,
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
    question = get_object_or_404(Question, id=question_id, sondage__creator=request.user)
    if request.method == 'POST':
        question.text = request.POST.get('text')
        question.type = request.POST.get('type')
        question.is_required = request.POST.get('is_required') == 'on'
        question.save()
        
        # Gérer les options pour les types à choix
        if question.type in ['radio', 'checkbox', 'select']:
            option_ids = request.POST.getlist('option_ids')
            option_texts = request.POST.getlist('option_texts')
            
            # Mise à jour des existantes
            for oid, otext in zip(option_ids, option_texts):
                if oid:
                    Option.objects.filter(id=oid, question=question).update(text=otext)
                elif otext.strip():
                    Option.objects.create(question=question, text=otext)
        
        return redirect('sondage_builder', sondage_id=question.sondage.id)
    
    return render(request, 'forms/question_form.html', {
        'question': question,
        'question_types': Question.QUESTION_TYPES
    })

@login_required
def question_delete(request, question_id):
    question = get_object_or_404(Question, id=question_id, sondage__creator=request.user)
    sondage_id = question.sondage.id
    if request.method == 'POST':
        question.delete()
    return redirect('sondage_builder', sondage_id=sondage_id)

@login_required
def option_delete(request, option_id):
    option = get_object_or_404(Option, id=option_id, question__sondage__creator=request.user)
    sondage_id = option.question.sondage.id
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
        response_obj = Response.objects.create(
            sondage=sondage,
            user=request.user if request.user.is_authenticated else None
        )
        
        for question in sondage.questions.all():
            answer = Answer.objects.create(response=response_obj, question=question)
            
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

from django.db.models import Count
from django.db.models.functions import TruncDay
import json
from django.core.serializers.json import DjangoJSONEncoder

@login_required
def sondage_results(request, sondage_id):
    try:
        sondage = Sondage.objects.get(id=sondage_id, creator=request.user)
    except Sondage.DoesNotExist:
        messages.error(request, "Accès refusé.")
        return redirect('dashboard')

    responses = sondage.responses.all().order_by('created_at')
    responses_count = responses.count()
    
    # --- Données pour le graphique d'évolution (Time Series) ---
    evolution_query = responses.annotate(day=TruncDay('created_at')) \
                               .values('day') \
                               .annotate(count=Count('id')) \
                               .order_by('day')
    
    evolution_labels = [item['day'].strftime('%d %b') for item in evolution_query]
    evolution_data = [item['count'] for item in evolution_query]

    questions = sondage.questions.all()
    questions_data = []
    
    for question in questions:
        data = {
            'question': question, 
            'answers_list': [],
            'chart_labels': [],
            'chart_data': []
        }
        
        if question.type in ['text', 'textarea']:
            data['answers_list'] = Answer.objects.filter(question=question).exclude(text_value='').values_list('text_value', flat=True)[:10]
        else:
            for option in question.options.all():
                count = Answer.objects.filter(question=question, selected_options=option).count()
                data['chart_labels'].append(option.text)
                data['chart_data'].append(count)
            
            # Formater les stats pour l'affichage classique aussi
            data['options_stats'] = [
                {'text': label, 'count': val, 'percentage': (val/responses_count*100 if responses_count > 0 else 0)} 
                for label, val in zip(data['chart_labels'], data['chart_data'])
            ]
            
        questions_data.append(data)

    # Préparation du tableau détaillé
    table_headers = [q.text for q in questions]
    table_rows = []
    for resp in responses.order_by('-created_at'):
        row = {'date': resp.created_at, 'answers': []}
        for q in questions:
            ans = Answer.objects.filter(response=resp, question=q).first()
            if ans:
                val = ans.text_value if q.type in ['text', 'textarea'] else ", ".join([o.text for o in ans.selected_options.all()])
                row['answers'].append(val or '-')
            else: row['answers'].append('-')
        table_rows.append(row)

    return render(request, 'forms/sondage_results.html', {
        'sondage': sondage,
        'responses_count': responses_count,
        'evolution_labels': json.dumps(evolution_labels),
        'evolution_data': json.dumps(evolution_data),
        'questions_data': questions_data,
        'table_headers': table_headers,
        'table_rows': table_rows,
    })

# Vue de connexion personnalisée sécurisée contre les emails multiples
def custom_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            
            # Gérer le cas où plusieurs utilisateurs ont le même email
            matching_users = User.objects.filter(email=email)
            
            if not matching_users.exists():
                form.add_error(None, 'Aucun compte trouvé avec cet email.')
            else:
                authenticated_user = None
                for u in matching_users:
                    user = authenticate(request, username=u.username, password=password)
                    if user is not None:
                        authenticated_user = user
                        break
                
                if authenticated_user:
                    login(request, authenticated_user)
                    return redirect('dashboard')
                else:
                    form.add_error(None, 'Mot de passe incorrect.')
    else:
        form = CustomLoginForm()
    return render(request, 'forms/login.html', {'form': form})

# Vue d'inscription
def signup(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = CustomUserCreationForm()
    return render(request, 'forms/signup.html', {'form': form})

# Vue de déconnexion
class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('home')

from django.http import JsonResponse
from django.views.decorators.http import require_POST

@login_required
@require_POST
def sondage_autosave(request, sondage_id):
    sondage = get_object_or_404(Sondage, id=sondage_id, creator=request.user)
    
    # Save Sondage Metadata
    title = request.POST.get('title')
    description = request.POST.get('description')
    if title: sondage.title = title
    if description is not None: sondage.description = description
    sondage.save()
    
    # Save Question Texts & Required status
    for key, value in request.POST.items():
        if key.startswith('q_text_'):
            q_id = key.replace('q_text_', '')
            Question.objects.filter(id=q_id, sondage=sondage).update(text=value)
        elif key.startswith('q_req_'):
            q_id = key.replace('q_req_', '')
            Question.objects.filter(id=q_id, sondage=sondage).update(is_required=(value == 'true'))
        elif key.startswith('opt_text_'):
            opt_id = key.replace('opt_text_', '')
            Option.objects.filter(id=opt_id, question__sondage=sondage).update(text=value)
            
    return JsonResponse({'status': 'success'})

@login_required
def question_add_ajax(request, sondage_id):
    sondage = get_object_or_404(Sondage, id=sondage_id, creator=request.user)
    q_type = request.GET.get('type', 'text')
    
    # Order calculation
    last_q = sondage.questions.order_by('order').last()
    order = (last_q.order + 1) if last_q else 0
    
    question = Question.objects.create(
        sondage=sondage,
        text="Nouvelle question",
        type=q_type,
        order=order
    )
    
    # Add default options
    if q_type in ['radio', 'checkbox', 'select']:
        Option.objects.create(question=question, text="Option 1")
    elif q_type == 'boolean':
        Option.objects.create(question=question, text="Oui")
        Option.objects.create(question=question, text="Non")
        
    return redirect('sondage_builder', sondage_id=sondage.id)

@login_required
def option_add_ajax(request, question_id):
    question = get_object_or_404(Question, id=question_id, sondage__creator=request.user)
    option = Option.objects.create(question=question, text="Nouvelle option")
    return JsonResponse({
        'status': 'success', 
        'option_id': option.id, 
        'option_text': option.text
    })

@login_required
@require_POST
def option_delete_ajax(request, option_id):
    option = get_object_or_404(Option, id=option_id, question__sondage__creator=request.user)
    option.delete()
    return JsonResponse({'status': 'success'})
def forgot_password(request):
    user = None
    if request.method == 'POST':
        if 'username' in request.POST:
            username = request.POST.get('username')
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                user = None
        elif 'new_password1' in request.POST and request.session.get('reset_user_id'):
            user_id = request.session['reset_user_id']
            user = User.objects.get(id=user_id)
            form = SetPasswordForm(user, request.POST)
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, user)
                request.session.pop('reset_user_id', None)
                return redirect('home')
            else:
                return render(request, 'forms/forgot_password.html', {'user': user, 'form': form})
    if user:
        request.session['reset_user_id'] = user.id
        form = SetPasswordForm(user)
        return render(request, 'forms/forgot_password.html', {'user': user, 'form': form})
    else:
        return render(request, 'forms/forgot_password.html', {'user': None})
