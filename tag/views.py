from django.contrib import messages
from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect
from .models import Tag, TagForm


def index(request):
    return render(request, 'tag/index.html', {'tags': Tag.objects.all()})


def new(request):
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            tag = form.save()
            messages.add_message(request, messages.SUCCESS, f'Tag {tag.name} was added')
            return redirect('tag:index')
    else:
        form = TagForm()

    return render(request, 'tag/new.html', {'form': form})


def edit(request, tag_id):
    try:
        tag = Tag.objects.get(pk=tag_id)
        form = TagForm(request.POST or None, instance=tag)
        if request.method == 'POST':
            if form.is_valid():
                tag = form.save()
                messages.add_message(request, messages.SUCCESS, f'Tag {tag.name} was updated')
                return redirect('tag:index')
        return render(request, 'tag/edit.html', {'form': form})
    except Tag.DoesNotExist:
        return HttpResponseNotFound()


def delete(request, tag_id):
    try:
        tag = Tag.objects.get(pk=tag_id)
        tag.delete()
        messages.add_message(request, messages.SUCCESS, f'Tag {tag.name} was deleted')
        return redirect('tag:index')
    except Tag.DoesNotExist:
        return HttpResponseNotFound()
