#Mirror from GitLab to GitHub by using the CI

If you wold like to mirror your GitLab Repo to GitHub you can use your `.gitlab-ci.yml` to automate this process.

Create a repository in GitHub where you would like to have your mirror.

Then create a [personal access token](https://help.github.com/articles/creating-a-personal-access-token-for-the-command-line/)
in for your GitHub account.

Add this `personal access token` as a [secret variable](https://docs.gitlab.com/ee/ci/variables/) to your GitLab repository.

Now you can access your GitHub account in the CI.

To use git in your CI define a job or job-template like this in ``.gitlab-ci.yml``:
```
mirror-github:
  script:
    - apk --no-cache add git
    - git push -u -f https://{GitHub-User-Name}:$CI_SECRET@github.com/{GitHub-User-Name}/{GitHub-Repo-Name}.git $CI_COMMIT_SHA:$CI_COMMIT_REF_NAME
```

Now you can mirror your each commit to GitHub.

**Nett to know**: You can also publish `gh-pages` from your GitLab repository by mirroring a the `gh-page`-branch to GitHub.