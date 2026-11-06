"""Talking to GitLab: the REST client, its Redis-backed cache and the token
health check the sync preflight runs. Nothing here is called during a page
render - data reaches pages through sync and webhooks."""
