# Deployment processes

For a reference of command meanings, see [COMMANDS.md](../COMMANDS.md)

Before running any deploy, you'll need to make sure:

- your current working directory in the terminal is in the umbrella repository
- your umbrella is configured with secrets, and the secrets are up-to-date
- you ahve run `workon largo` or its equivalent to load the virtualenv you use with the deploy tools

Here's a table of contents of this page:

- Deploy, short version
- Normal deploy, explained
- Deploy a site for the first time via SFTP
- Deploy fails with "failed to resolve ... as a valid commit"
- Deploying to a site that has been edited outside of version control


## Deploy, short version

Deploying staging

```
workon largo
git checkout staging
git pull
git push
fab staging branch:staging dry_run deploy
fab staging branch:staging deploy
```

Deploying production, after merging staging into master:

```
workon largo
git checkout master
git pull
git push
fab production branch:master dry_run deploy
fab production branch:master deploy
```

And then go clear the CDN caches.

## Normal deploy, explained

Let's test-deploy the 'staging' branch to the staging environment. This doesn't upload anything, but just makes sure that everything can be uploaded.

	fab staging branch:staging dry_run deploy

That should come out without any warnings or errors. Time to deploy to staging for real:

	fab staging branch:staging deploy

Of course, if you wanted to deploy the master branch to production, you'd do this:

	fab staging branch:master deploy

Or, to save a few keystrokes, there's the `master` alias, which runs `branch:master`:

	fab staging master deploy

When it comes time to deploy to production:

	fab production master dry_run deploy
	fab production master deploy

After deploying to production, be sure to clear the production CDN caches.

## Deploy a site for the first time via SFTP

```
curl: (78) Could not open remote file for reading: No such file or directory
```

This error is caused by the directories occupied by submodules not existing on the remote server. Until [#52](https://github.com/INN/deploy-tools/issues/52) is fixed, the initial deploy must be done by hand.

To deploy over SFTP by hand:

1. Using the hostname, username, and password referenced in your project's `fabfile.py`, connect to the server via SFTP using an SFTP client such as FileZilla or Cyberduck.
2. From your local copy of the repository, copy the directories containing any git submodules into their appropriate parent directories on the server.
3. Try running a deploy using `fab`, and make a note of any errors occur.

## Deploy fails with "failed to resolve ... as a valid commit"

```
fatal: Failed to resolve 'foo' as a valid ref.
fatal: Failed to resolve '6062fde88cbd1823be1fa7d0d1ef6cc8e1e6a0ef' as a valid ref.
```

When deploying, the `deploy` task makes a note of the commit that is currenly deployed on the remote server and tags that commit with the `rollback` tag. (See [git tag](https://git-scm.com/book/en/v2/Git-Basics-Tagging))

If the commit hash saved in the `.git-ftp.log` file on the server is not available in the local copy of the repository, then you will see this error.

First, run `git pull` to make sure that you have all commits from the upstream version of this repository. You may need to resolve merge conflicts if there are commits upstream that did not exist locally.

If the commit hash from `.git-ftp.log` is not in any repository you have access to, well, it looks like someone deployed without pushing. Ask everyone to push their work, please.

If no one has the work in question, you have three options:

1. Don't deploy today.
2. Deploy files by hand using an SFTP client.
3. Using an SFTP client, delete all `.git-ftp.log` files from the remote server.

## Deploying to a site that has been edited outside of version control

If the site you are deploying to has been edited outside of the version-control workflow, you have two options: ignore the changes and redeploy, or incorporate the changes into version control and then redeploy.

To ignore the changes, proceed with a normal deploy as described under "Simple Deploy"

To incorporate the changes:

1. Using an SFTP client, copy all files from production that are relevant to this project:
	- any file tracked in your local copy of the repository
	- any file found in a folder the contents of which are tracked by the repository
2. Run `git status` to see what files have changed. Use that and `git diff` to decide whether to keep or discard changes from the remote server.
3. Commit the changes you would like to keep.
4. Push your changes to GitHub
5. Deploy, following the normal deploy process.
