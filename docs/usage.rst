========
Usage
========

.. code-block:: python

   # models.py
   class Blog(models.Model)
       ...

   class BlogEntry(models.Model):
       blog = models.ForeignKey(Blog)


   # views.py
   from drf_nested_resource.mixins import NestedResourceMixin


   class BlogEntryViewSet(NestedResourceMixin, ...):
       model = BlogEntry
       parent_model = Blog

   # urls.py
   urlpatterns = patterns('',  # NOQA
       url(
           r'^blogs/(?P<blog_pk>\d+)/entries/$', views.BlogEntryViewSet.as_view(),
       ),
   )
