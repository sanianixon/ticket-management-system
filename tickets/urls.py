from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


from .views import (
    ProjectViewSet,
    TicketViewSet,
    CommentViewSet,
    TicketHistoryViewSet,
    DashboardSummaryAPIView,
    TicketManualAPIView,
    LoginAPIView,
    LogoutAPIView,
    CurrentUserAPIView,
    UserListAPIView,
)

router = DefaultRouter()

router.register("projects", ProjectViewSet)
router.register("tickets", TicketViewSet)
router.register("comments", CommentViewSet)
router.register("ticket-history", TicketHistoryViewSet)

urlpatterns = [
    path("dashboard-summary/", DashboardSummaryAPIView.as_view()),
    path("manual-tickets/", TicketManualAPIView.as_view()),
    path("manual-tickets/<int:pk>/", TicketManualAPIView.as_view()),
    path("", include(router.urls)),
    path("login/", LoginAPIView.as_view()),
    path("logout/", LogoutAPIView.as_view()),
    path("current-user/", CurrentUserAPIView.as_view()),
    path("users/", UserListAPIView.as_view()),
    path("token/", TokenObtainPairView.as_view()),
    path("token/refresh/", TokenRefreshView.as_view()),
]