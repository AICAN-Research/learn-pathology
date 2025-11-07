from django.conf.urls.static import static
from django.urls import path, include
from django.contrib.auth import views as auth_views
import os
from learnpathology import settings
from slide import views

app_name = 'slide'
urlpatterns = [
    path('list/', views.index, name='list'),
    path('browser/', views.image_browser, name='browser'),
    path('browser/reset', views.reset_image_browser, name='browser_reset'),
    #path('browser/grid-view', views.grid_view, name='grid_view'),
    #path('browser/list-view', views.list_view, name='list_view'),
    path('view/<int:slide_id>/', views.whole_slide_view_full, name='view_full'),
    path('view/<int:slide_id>/<int:course_id>', views.whole_slide_view_full, name='view_full'),
    path('edit-tags/<int:slide_id>', views.edit_general_pathology_tags, name='edit_tags'),
    path('add-tag/', views.add_tag, name='add_tag'),
    path('remove-tag/', views.remove_tag, name='remove_tag'),
    # Annotation stuff
    path('annotation/create/', views.create_annotation, name='create_annotation'),
    path('annotation/update/', views.update_annotation, name='update_annotation'),
    path('annotation/delete/', views.delete_annotation, name='delete_annotation'),
    path('upload/', views.upload_slides, name='upload_slides'),
    path('upload/process/', views.process_uploaded_slides, name='process_uploads'),
    path('upload/view/', views.view_uploaded_slides, name='view_uploads'),
    path('edit/<int:slide_id>', views.edit_slide_metadata, name='edit_metadata'),
] + static('thumbnails/', document_root=settings.SLIDE_THUMBNAILS_DIR) \
  + static('uploads/thumbnails/', document_root=os.path.join(settings.TEMP_UPLOADED_SLIDE_DIR, 'thumbnails'))

