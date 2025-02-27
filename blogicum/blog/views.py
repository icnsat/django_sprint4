from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from django.db.models import Count
from django.views.generic import ListView, DetailView
from django.http import HttpResponseForbidden
from django.http import Http404
from django.utils import timezone

from .models import Post
from .models import Category
from .models import User
from .models import Comment

from .forms import EditProfileForm
from .forms import EditPostForm
from .forms import CommentForm
from .forms import PostForm


class PostListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'blog/index.html'

    def get_queryset(self):
        return Post.objects.annotate(comment_count=Count('comments')).filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category__is_published=True
        ).order_by('-pub_date')


class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/detail.html'  # Укажите ваш шаблон
    context_object_name = 'post'

    def get_object(self, queryset=None):
        post = super().get_object(queryset)

        # Проверяем, является ли текущий пользователь автором поста
        if (
            self.request.user != post.author
            and (
                not post.is_published
                or not post.category.is_published
                or post.pub_date >= timezone.now()
            )
        ):
            raise Http404("Пост не найден или недоступен.")

        return post

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        context['comments'] = post.comments.all()
        context['form'] = CommentForm()

        return context


class CategoryPostsListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'blog/category.html'

    def get_queryset(self):
        """Return posts for the specified category."""
        category = self.kwargs['category']

        # Validate category
        category = get_object_or_404(Category, slug=category)

        if not category.is_published:
            raise Http404()

        # Get related posts
        return Post.objects.select_related('category').annotate(
            comment_count=Count('comments')
        ).filter(
            pub_date__lte=timezone.now(),
            is_published=True,
            category=category
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        """Add category to context."""
        context = super().get_context_data(**kwargs)
        context['category'] = get_object_or_404(
            Category,
            slug=self.kwargs['category']
        )
        return context


class ProfileListView(ListView):
    model = Post
    paginate_by = 10
    template_name = 'blog/profile.html'

    def get_queryset(self):
        username = self.kwargs['username']

        return Post.objects.annotate(
            comment_count=Count('comments')
        ).filter(
            author__username=username
        ).order_by('-pub_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['profile'] = get_object_or_404(
            User,
            username=self.kwargs['username']
        )
        return context


@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = EditProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()

    else:
        form = EditProfileForm(instance=request.user)
    return render(request, 'blog/user.html', {'form': form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return redirect('blog:post_detail', pk=post.id)

    if request.method == 'POST':
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            form.save()  # Сохраняем изменения
            return redirect('blog:post_detail', pk=post.id)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/create.html', {
        'form': form,
        'post': post,
    })


@login_required
def create_post(request):
    if request.method == 'POST':
        form = EditPostForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=request.user.username)

    else:
        form = EditPostForm(user=request.user)

    return render(request, 'blog/create.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect(
                'blog:post_detail',
                pk=post.id)  # Перенаправляем на страницу поста
    else:
        return HttpResponseForbidden("Неверный метод запроса")

    return redirect('blog:post_detail', pk=post.id)


@login_required
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    # Проверяем, является ли текущий пользователь автором комментария
    if request.user != comment.author:
        return HttpResponseForbidden(
            "У вас нет прав для редактирования этого комментария."
        )

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()  # Сохраняем изменения
            return redirect('blog:post_detail', pk=post_id)
    else:
        form = CommentForm(instance=comment)

    return render(request, 'blog/comment.html', {
        'form': form,
        'comment': comment,
    })


@login_required
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, post_id=post_id)

    # Проверяем, является ли текущий пользователь автором комментария
    if request.user != comment.author:
        return HttpResponseForbidden(
            "У вас нет прав для удаления этого комментария."
        )

    if request.method == 'POST':
        comment.delete()  # Удаляем комментарий
        return redirect('blog:post_detail', pk=post_id)

    return render(request, 'blog/comment.html', {
        'comment': comment,
    })


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.user != post.author:
        return HttpResponseForbidden(
            "У вас нет прав для удаления этого поста."
        )

    if request.method == 'POST':
        post.delete()  # Удаляем пост
        return redirect('blog:index')  # Перенаправляем на главную страницу

    # Передаем форму в шаблон для отображения информации о посте
    form = PostForm(instance=post)  # Заполняем форму текущими данными поста

    return render(request, 'blog/create.html', {
        'form': form,
        'post': post,
    })
