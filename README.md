# Wush

## A simple django app that handles mobile and web push notifications

### Install

* Install through `pip`:

  ```
  pip install -e git+git://github.com/theju/wush.git#egg=wush
  ```
  
  Or follow the setups below

* Clone the git repo:

  ```
  git clone https://github.com/theju/wush
  cd wush
  ```
* Install the dependencies listed in the `requirements.txt`:

  ```
  pip install -r requirements.txt
  ```
  
### Setup

* Reference this app in your project's `settings.py`:

  ```
  INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    ...

    'wush',
    ...
  )
  ```
* Add the other required settings variables:

  ```
  REDIS_HOST = "localhost"
  REDIS_PORT = 6379
  APNS_CERTFILE = "/path/to/apns_cert.pem"
  APNS_TOPIC = "<com.app.bundlename>"
  GCM_URL = "https://gcm-http.googleapis.com/gcm/send"
  GCM_KEY = "..."
  ```
* Reference the urls from the app into your project:

  ```
  url(r'^push/', include('wush.urls')),
  ```	
* Create the required tables through the `migrate` command:

  ```
  python manage.py migrate
  ```
* The push tokens that are fetched from the mobile devices need to
  be stored into the `DeviceToken` model. For example:

  ```
  token = DeviceToken.objects.create(
      user = some_user,
      token = "<token_from_mobile_device>",
	  platform = "<android|ios|firefox|chrome>"
  )
  ```
* Perform an HTTP Post request onto the `/push/notify/` URL with the
  `to` (username) and `body` (message of the notification; should be a JSON
  object) params to send out a push notification to that `username` on all
  their devices. Example

  ```
  requests.post("/push/notify/", data={
      "to": "<some_username>", "body": "{\"title\": \"Message of the push notification\"}"
  })
  ```
