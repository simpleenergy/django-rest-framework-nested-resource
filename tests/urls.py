from rest_framework.routers import SimpleRouter

from . import views


router = SimpleRouter()
router.register(
    'targets/(?P<target_pk>\d+)/sources',
    views.NestedForeignKeySourceModelViewSet, 'nested-sources',
)
router.register(
    'targets/(?P<target_model_pk>\d+)/generic-sources',
    views.NestedGenericForeignKeySourceModelViewSet, 'nested-generic-sources',
)
router.register(
    'm2m-targets/(?P<target_pk>\d+)/m2m-sources',
    views.NestedManyToManySourceModelViewSet, 'nested-m2m-sources',
)
router.register(
    'm2m-sources/(?P<source_pk>\d+)/m2m-targets',
    views.NestedManyToManyTargetModelViewSet, 'nested-m2m-targets',
)

urlpatterns = router.urls
