import argparse
import logging

# Install via: pip install GitPython
from git import Repo

logging.basicConfig(level=logging.INFO)

def parse_args():
    parser = argparse.ArgumentParser(description='Pull latest commits from dmlc/tvm')
    parser.add_argument('--sum', dest='accumulate', action='store_const',
                    const=sum, default=max,
                    help='sum the integers (default: find the max)')

    return parser.parse_args()

def add_remote(repo, name, url):
    for remote in repo.remotes:
        if remote.name == name:
            assert remote.url == url
            logging.info("Remote {} already exists".format(name))
            return
    logging.info("Add remote {} with url {}".format(name, url))
    repo.create_remote(name, url)

"""
This tool automatically cherry picks commit from dmlc/tvm into neo-ai/tvm's dev
branch, it keeps track of last selected commit id in file dmlc_tvm_commit_id. It
fetches from dmlc/tvm first, get the latest commit id from master branch, and cherry-picks
commits from last slected commit until latest commit. 
"""
def main():
    args = parse_args()
    last_commit_file = 'dmlc_tvm_commit_id'
    last_commit = None
    with open(last_commit_file) as f:
        last_commit = f.read().strip()
    if last_commit is None:
        logging.error('can not find last commit file {}'.format(last_commit_file))
    logging.info('Synchronizing from commit {}'.format(last_commit))

    # Add dmlc/tvm to remote 'upstream' if not
    repo = Repo()
    add_remote(repo, 'upstream', 'git@github.com:dmlc/tvm.git')

    # Fetch 'upstream' remote
    logging.info("Fetching remote upstrean")
    upstream = repo.remote('upstream')
    upstream.fetch()

    # Switch to 'master' in 'upstream'
    repo.git.checkout('upstream/master')

    # Save HEAD commit
    head = repo.commit('HEAD')
    head_commit = head.hexsha

    # Switch back to 'dev' branch to do cherry pick
    repo.git.checkout('dev')

    # Do the cherry-pick from last_commit to head_commit
    repo.git.cherry_pick('{}..{}'.format(last_commit, head_commit))

    # Update submodule
    repo.git.submodule('update')

    with open(last_commit_file, 'w') as f:
        f.write(head_commit)

    logging.info("Update successfully")

if __name__ == '__main__':
    main()
