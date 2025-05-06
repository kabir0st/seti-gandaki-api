from core.utils.permissions import (IsStaff, IsStaffOrCreateOnly,
                                    IsStaffOrReadOnly)
from core.utils.viewsets import DefaultViewSet, SingletonViewSet
from system.apis.filtersets.misc import DocumentFilterSet
from system.models.misc import FAQ, Document, Inquiries
from system.models.settings import GlobalSettings
from system.serializers.misc import (DocumentSerializer, FAQSerializer,
                                     GlobalSettingsSerializer,
                                     InquiriesSerializer)


class DocumentAPI(DefaultViewSet):
    queryset = Document.objects.all().order_by('-id')
    serializer_class = DocumentSerializer
    search_fields = ["name", 'model']
    filterset_class = DocumentFilterSet
    permission_classes = [IsStaff]

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset()


class FAQAPI(DefaultViewSet):
    queryset = FAQ.objects.all().order_by('-id')
    serializer_class = FAQSerializer
    permission_classes = [IsStaffOrReadOnly]

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter()


class GlobalSettingsAPI(SingletonViewSet):
    queryset = GlobalSettings.objects.filter().order_by('-id')
    serializer_class = GlobalSettingsSerializer
    permission_classes = [IsStaffOrReadOnly]


class InquiriesAPI(SingletonViewSet):
    queryset = Inquiries.objects.filter().order_by('-id')
    serializer_class = InquiriesSerializer
    permission_classes = [IsStaffOrCreateOnly]
