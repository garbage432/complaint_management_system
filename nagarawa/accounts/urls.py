from django.urls import path
from . import views
app_name = 'accounts'

urlpatterns = [
    path('register/',                           views.register_view,         name='register'),
    path('login/',                              views.login_view,            name='login'),
    path('logout/',                             views.logout_view,           name='logout'),
    path('profile/<str:username>/',             views.profile_view,          name='profile'),
    path('profile/edit/me/',                    views.profile_edit_view,     name='profile_edit'),
    path('deptadmin/',                          views.deptadmin_dashboard,   name='deptadmin_dashboard'),
    path('superadmin/',                         views.superadmin_dashboard,  name='superadmin_dashboard'),
    path('user/',                               views.user_dashboard,        name='user_dashboard'),
    path('role-redirect/',                      views.role_redirect,         name='role_redirect'),

    # Dept admin actions
    path('complaint/<int:pk>/update-status/',   views.update_status,         name='update_status'),
    path('complaint/<int:pk>/add-note/',        views.add_internal_note,     name='add_note'),
    path('complaint/<int:pk>/assign/',          views.assign_complaint,      name='assign_complaint'),
    path('complaint/<int:pk>/notify-author/',   views.notify_author,         name='notify_author'),
    path('complaint/<int:pk>/set-priority/',    views.set_priority,          name='set_priority'),
    path('export/csv/',                         views.export_csv,            name='export_csv'),

    # Citizen actions
    path('complaint/<int:pk>/rate/',            views.rate_complaint,        name='rate_complaint'),
    path('complaint/<int:pk>/withdraw/',        views.withdraw_complaint,    name='withdraw_complaint'),

    # Platform
    path('stats/',                              views.public_stats,          name='public_stats'),
    path('notifications/',                      views.notifications_view,    name='notifications'),
    path('notifications/read/<int:pk>/',        views.mark_notification_read,name='notification_read'),
]