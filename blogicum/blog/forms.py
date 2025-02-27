# forms.py
from django import forms
from django.contrib.auth.models import User

from .models import Post
from .models import Comment


class EditProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']


class EditPostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'image', 'pub_date', 'location', 'category']

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super(EditPostForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        post = super(EditPostForm, self).save(commit=False)
        if self.user:
            post.author = self.user
        if commit:
            post.save()
        return post


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'image',
                  'location', 'category', 'is_published']
        widgets = {
            'text': forms.Textarea(
                attrs={'rows': 5, 'placeholder': 'Введите текст поста...'}),
            'title': forms.TextInput(
                attrs={'placeholder': 'Введите заголовок поста...'}),
            'image': forms.ClearableFileInput(
                attrs={'class': 'form-control-file'}),
            'location': forms.Select(
                attrs={'class': 'form-control'}),
            'category': forms.Select(
                attrs={'class': 'form-control'}),
            'is_published': forms.CheckboxInput(
                attrs={'class': 'form-check-input'}),
        }
