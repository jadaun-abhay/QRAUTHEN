from rest_framework import status

# Write your status here

success_status_mapping = {
    "get": status.HTTP_200_OK,
    "post": status.HTTP_201_CREATED,
    "put": status.HTTP_200_OK,
    "delete": status.HTTP_200_OK,
}
