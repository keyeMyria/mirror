# Mirror 

This is a mirror from GitLab to GitHub

Follow the steps to create a mirror from a certain GitLab-Repo to GitHub.

* Create a GitLab-Repo.
* Create a GitHub-Repo.
* Overload the default origin of your GitLab-Repo to reference the GitLab and GitHub by using:
```
$ git remote set-url --add origin https.//github/<your-user-name>/<your-repo>.git
```

By using:
```
$ git push origin <branch>
```
there will be a push to GitHub and to GitLab.
