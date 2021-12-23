Low-volume APNs Support In Python 3
===================================

This repo provides fully functional code to use Apple's push notification
service. Only their current, HTTP/2 interface, using JWT authentication is
supported.

This uses a single request per push, which is against Apple's recommendation,
but is the same as Google's push system (FCM), so can't be that bad.

There's no license just add the code to your project if it's useful.

Cheers!
