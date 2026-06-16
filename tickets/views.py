from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from django.contrib.auth import authenticate, login, logout
from rest_framework.permissions import AllowAny
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from .serializers import CustomUserSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.mail import send_mail
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken


from .models import Project, Ticket, Comment, TicketHistory
from .serializers import (
    ProjectSerializer,
    TicketSerializer,
    CommentSerializer,
    TicketHistorySerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

class TicketViewSet(viewsets.ModelViewSet):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["status", "priority", "project", "assigned_to"]
    search_fields = ["title", "description"]

    @action(detail=True, methods=["get"])
    def comments(self, request, pk=None):
        ticket = self.get_object()
        comments = ticket.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        ticket = self.get_object()
        history = ticket.history.all()
        serializer = TicketHistorySerializer(history, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

class TicketHistoryViewSet(viewsets.ModelViewSet):
    queryset = TicketHistory.objects.all()
    serializer_class = TicketHistorySerializer

class DashboardSummaryAPIView(APIView):

    def get(self, request):
        data = {
            "total_projects": Project.objects.count(),
            "total_tickets": Ticket.objects.count(),
            "open_tickets": Ticket.objects.filter(status="OPEN").count(),
            "in_progress_tickets": Ticket.objects.filter(status="IN_PROGRESS").count(),
            "resolved_tickets": Ticket.objects.filter(status="RESOLVED").count(),
            "closed_tickets": Ticket.objects.filter(status="CLOSED").count(),
        }

        return Response(data)
    



class TicketManualAPIView(APIView):

    def custom_response(
        self,
        success,
        data=None,
        errors=None,
        status_code=status.HTTP_200_OK
    ):
        response_data = {
            "success": success
        }

        if data is not None:
            response_data["data"] = data

        if errors is not None:
            response_data["errors"] = errors

        return Response(response_data, status=status_code)


    def validate_ticket_business_rules(self, data, existing_ticket=None):
        title = data.get("title")
        status_value = data.get("status")
        priority = data.get("priority")
        assigned_to = data.get("assigned_to")

        if title is not None and len(title.strip()) < 5:
            return "Title must be at least 5 characters long."

        if existing_ticket is None and status_value == "CLOSED":
            return "New ticket cannot be created directly as CLOSED."

        if priority == "CRITICAL" and not assigned_to:
            return "Critical priority tickets must be assigned to a user."

        if existing_ticket and existing_ticket.status == "CLOSED":
            return "Closed tickets cannot be updated."

        return None


    def get(self, request, pk=None):
        if pk:
            try:
                ticket = Ticket.objects.get(pk=pk)
            except Ticket.DoesNotExist:
                return self.custom_response(
                    success=False,
                    errors="Ticket not found",
                    status_code=status.HTTP_404_NOT_FOUND
                )

            serializer = TicketSerializer(ticket)

            return self.custom_response(
                success=True,
                data=serializer.data
            )

        if request.user.role == "ADMIN":
            tickets = Ticket.objects.all()
        else:
            tickets = Ticket.objects.filter(assigned_to=request.user)

        serializer = TicketSerializer(tickets, many=True)

        return self.custom_response(
            success=True,
            data={
                "count": len(serializer.data),
                "tickets": serializer.data
            }
        )


    def post(self, request):
        error = self.validate_ticket_business_rules(request.data)

        if error:
            return self.custom_response(
                success=False,
                errors=error,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer = TicketSerializer(data=request.data)

        if serializer.is_valid():
            ticket = serializer.save()

            if ticket.assigned_to and ticket.assigned_to.email:
                send_mail(
                    subject="New Ticket Assigned",
                    message=f"You have been assigned a new ticket: {ticket.title}",
                    from_email=None,
                    recipient_list=[ticket.assigned_to.email],
                    fail_silently=False,
    )
            return self.custom_response(
                success=True,
                data=serializer.data,
                status_code=status.HTTP_201_CREATED
            )

        return self.custom_response(
            success=False,
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


    def put(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return self.custom_response(
                success=False,
                errors="Ticket not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        error = self.validate_ticket_business_rules(request.data, ticket)

        if error:
            return self.custom_response(
                success=False,
                errors=error,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer = TicketSerializer(ticket, data=request.data)

        if serializer.is_valid():
            serializer.save()

            return self.custom_response(
                success=True,
                data=serializer.data
            )

        return self.custom_response(
            success=False,
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


    def patch(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return self.custom_response(
                success=False,
                errors="Ticket not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        error = self.validate_ticket_business_rules(request.data, ticket)

        if error:
            return self.custom_response(
                success=False,
                errors=error,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        serializer = TicketSerializer(ticket, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()

            return self.custom_response(
                success=True,
                data=serializer.data
            )

        return self.custom_response(
            success=False,
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


    def delete(self, request, pk):
        try:
            ticket = Ticket.objects.get(pk=pk)
        except Ticket.DoesNotExist:
            return self.custom_response(
                success=False,
                errors="Ticket not found",
                status_code=status.HTTP_404_NOT_FOUND
            )

        ticket.delete()

        return self.custom_response(
            success=True,
            data="Ticket deleted successfully"
        )


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")

        if not username or not password:
            return Response({
                "success": False,
                "message": "Username and password are required"
            }, status=status.HTTP_400_BAD_REQUEST)

        User = get_user_model()

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "Invalid username or password"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not check_password(password, user.password):
            return Response({
                "success": False,
                "message": "Invalid username or password"
            }, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_active:
            return Response({
                "success": False,
                "message": "User account is inactive"
            }, status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)

        return Response({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            },
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            }
        }, status=status.HTTP_200_OK)
    
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response({
                "success": False,
                "message": "Refresh token is required"
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({
                "success": True,
                "message": "Logged out successfully"
            }, status=status.HTTP_200_OK)

        except Exception:
            return Response({
                "success": False,
                "message": "Invalid or expired token"
            }, status=status.HTTP_400_BAD_REQUEST)


class CurrentUserAPIView(APIView):

    def get(self, request):
        user = request.user

        return Response({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "role": user.role,
            }
        })


class UserListAPIView(APIView):

    def get(self, request):
        User = get_user_model()
        users = User.objects.all()

        serializer = CustomUserSerializer(users, many=True)

        return Response({
            "success": True,
            "data": serializer.data
        })



