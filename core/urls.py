from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('telegram/', include('bot.urls')),
    path('', include('shop.urls')),
]

# Media is intentionally served by Django only in DEBUG/local development.
# On Render, uploaded media is ephemeral; see DEPLOY.md for persistent storage options.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
