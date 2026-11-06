"""The classroom assistant - a bot that works on the course's projects as a
colleague would: it reviews pushes, plants a merge conflict for the branching
exercise, and runs the issues-and-merge-requests exercise from the issue it
assigns to the merge it approves.

Students meet it only in GitLab (comments, a commit, issues); teachers set it
up and follow it on the course's Assistant page. It acts under its own bot
account and token (``models/assistant.py``) - the analytics keep their
read-only token and never write.
"""
