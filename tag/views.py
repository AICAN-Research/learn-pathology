from django.contrib import messages
from django.http import HttpResponseNotFound
from django.shortcuts import render, redirect
from tag.models import Tag, TagForm, DeleteTagForm
from user.decorators import teacher_required


def index(request):
    tags = Tag.objects.all()
    selected_organs = request.GET.get('organs', False)
    selected_stains = request.GET.get('stains', False)
    selected_others = request.GET.get('others', False)

    if not selected_organs and not selected_stains and not selected_others:
        selected_organs = True
        selected_stains = True
        selected_others = True
        tags = Tag.objects.all()
    else:  # at least one of the categories is selected
        tags = Tag.objects.none()
        if selected_organs:
            tags = tags.union(Tag.objects.filter(is_organ=True))
        if selected_stains:
            tags = tags.union(Tag.objects.filter(is_stain=True))
        if selected_others:
            tags = tags.union(Tag.objects.filter(is_organ=False, is_stain=False))

    context = {
        'tags': tags,
        'selected_organs': selected_organs,
        'selected_stains': selected_stains,
        'selected_others': selected_others,
    }

    return render(request, 'tag/index.html', context)


@teacher_required
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


@teacher_required
def edit(request, tag_id):
    try:
        tag = Tag.objects.get(pk=tag_id)
        form = TagForm(request.POST or None, instance=tag)
        if request.method == 'POST':
            if form.is_valid():
                tag = form.save()
                messages.add_message(request, messages.SUCCESS, f'Tag {tag.name} was updated')
                return redirect('tag:index')
        return render(request, 'tag/edit.html', {'form': form, 'tag': tag})
    except Tag.DoesNotExist:
        return HttpResponseNotFound()


@teacher_required
def delete(request, tag_id):
    """
    View to delete a tag from the database
    """

    if request.method == 'POST':  # Form was submitted
        form = DeleteTagForm(request.POST)
        if form.is_valid():
            tag = Tag.objects.get(id=tag_id)
            if form.cleaned_data['confirmDelete']:
                tag.delete()
                messages.add_message(request, messages.SUCCESS, f'The tag {tag.name} was deleted')
            else:
                messages.add_message(request, messages.SUCCESS, f'The tag {tag.name} was not deleted')
            return redirect('tag:index')

    else:  # GET method
        # Render page with tag info and "Delete? Yes/No"
        if tag_id in Tag.objects.all().values_list('id', flat=True):
            tag = Tag.objects.all().get(id=tag_id)
            return render(request, 'tag/delete.html',
                          {'form': DeleteTagForm(), 'tag': tag})

        else:  # In case user enters invalid URL directly
            messages.add_message(request, messages.WARNING, 'Did not find tag')
            return redirect('tag:index')

    return redirect('tag:index')
