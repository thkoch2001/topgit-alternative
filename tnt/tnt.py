from yaml import load, dump
try:
    from yaml import CLoader as Loader
    from yaml import CDumper as Dumper
except ImportError:
    from yaml import Loader, Dumper

import git

# TODO: Check the yaml.safe_load function
# data = load(stream, Loader=Loader)
# output = dump(data, Dumper=Dumper)

def git_has_head( repo, searchedHead ):
    heads = repo.heads
    for head in heads:
        if searchedHead == head.name:
            return True
    return False

def to_YAML( patchset ):
    return dump( patchset.serialize(), Dumper=Dumper )

def from_YAML( stream ):
    yaml = load( stream, Loader=Loader )
    return PatchSet.unserialize( yaml )


class PatchBranch(object):
    """A branch that's part of a patchset

    dependencies: other branches of the same patchset this patch depends on
    """

    def __init__(self, commit=None, dependencies=[]):
        self.commit = commit
        self.dependencies = dependencies

    def serialize( self ):
        return {
            'commit'  : self.commit,
            'dependencies': self.dependencies
        }

    @classmethod
    def unserialize( cls, struct ):
        instance = cls()
        instance.commit = struct["commit"]
        instance.dependencies = struct["dependencies"]
        return instance

class PatchSet(object):
    """Represents a patchset

    branch: The branch that tracks the patchset
    """ 

    def __init__(self):
        self.root_commit = None
        self.root_name = None

    def has_branch(self, branch_name):
        return branch_name in self.branches

    def add_branch(self, branch_name, patch_branch):
        if self.has_branch(branch_name):
            print "branch already in patchset: "+branch_name
            exit(1)

        self.branches[branch_name] = patch_branch

        self.branches = {}

    def serialize( self ):
        branches = {};
        for branch in self.branches:
            branches[branch] = self.branches[branch].serialize()
        return{
            'root_commit': self.root_commit,
            'root_name': self.root_name,
            'branches': branches
        }

    @classmethod
    def unserialize( cls, struct ):
        instance = cls()
        branches = {}
        if "branches" in struct:
            for branch_name in struct["branches"]:
                branches[branch_name] = PatchBranch.unserialize( struct["branches"][branch_name] )
        instance.branches = branches
        instance.root_commit = struct["root_commit"]
        instance.root_name = struct["root_name"]
        return instance

    @classmethod
    def from_git_tree(cls, tree):
        branches_data = tree["branches"].data
        patchset = from_YAML(branches_data)
        return patchset

import tempfile
import shutil
import os

class GitHiddenCheckout(object):
    class VarToFile(object):
        def __init__(self, content, suffix=""):
            (low_level_handle, self.path) = tempfile.mkstemp(prefix="tnt", suffix=suffix)
            f = os.fdopen(low_level_handle,"w")
            f.write(content)
            f.close()
            self.f = open(self.path, "r" )

        def __del__(self):
            self.f.close()
            os.remove(self.path)

    def __init__(self, repo, branch):
        self.repo = repo
        self.branch = branch
        self.temp_dir = tempfile.mkdtemp(prefix="tnt")
        self.Git = git.Git(self.temp_dir)
        self.parents = []

        # TODO: allow to provide this info as constructor parameter
        if git_has_head(repo, branch):
            self.init_index()
            self.parents.append(branch)

    def init_index(self):
        index = self.repo.git.ls_tree(self.branch, r=True, full_name=True)
        indexHandle = self.VarToFile(index)
        self.setEnvironment()
        self.Git.update_index(index_info=True,istream=indexHandle.f)
        self.unsetEnvironment()

    def file_put_contents(self,name,content):
        full_path = self.to_full_path(name)
        f = open(full_path, "w")
        try:
            f.write(content)
        finally:
            f.close()

    def to_full_path(self,name):
        #check for ".." and alikes
        return os.path.join(self.temp_dir,name)

    def edit_file(self,name):
        os.system("vim " + self.to_full_path(name))

    def add(self,name):
        """adds a file to the index"""
        self.setEnvironment()
        self.Git.update_index("--add",name)
        self.unsetEnvironment()

    def commit(self, message):
        self.setEnvironment()
        tree_sha1 = self.Git.write_tree()
        parentOptions = []
        for parent in self.parents:
            parentOptions.append("-p")
            parentOptions.append(parent)

        messageHandle = self.VarToFile(message)
        commit_sha1 = self.Git.commit_tree(tree_sha1, istream=messageHandle.f, *parentOptions)
        self.Git.update_ref("refs/heads/"+self.branch, commit_sha1)
        self.unsetEnvironment()

    def setEnvironment(self):
        #TODO: eventually save values that may be there
        os.environ["GIT_INDEX_FILE"] = os.path.join(self.temp_dir, "index")
        os.environ["GIT_DIR"] = self.repo.path

    def unsetEnvironment(self):
        os.environ.pop("GIT_INDEX_FILE")
        os.environ.pop("GIT_DIR")

    def _clean(self):
        pass
        # shutil.rmtree(self.temp_dir,false,self.onCleanError)

    def onCleanError(function, path, excinfo):
        #If onerror is provided, it must be a callable that accepts three parameters:
        #function, path, and excinfo. The first parameter, function, is the function
        #which raised the exception; it will be os.path.islink(), os.listdir(),
        #os.remove() or os.rmdir(). The second parameter, path, will be the path name
        #passed to function. The third parameter, excinfo, will be the exception
        #information return by sys.exc_info(). Exceptions raised by onerror will not be
        #caught.  
        print "error while cleaning up: "
