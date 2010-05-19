from optparse import OptionParser
from tnt import *
import git
import os
import os.path
import urllib

class cli(object):
    __version__ = '0.0.1alpha'
    usage = "tnt - this is not topgit"

class InitCommand(object):
    def main( self, argv ):
        self.parse(argv)
        self.run()

    def getParser( self ):
        parser = OptionParser()
        return parser

    def parse( self, argv ):
        parser = self.getParser()
        (options, args) = parser.parse_args(args = argv)
        if len(args) != 1:
            print "fail"
            parser.error("no branch name for the patchset branch given")

        self.patchset_name = args[0]

    def run( self ):
        repo = git.Repo(os.getcwd())
        if git_has_head(repo, self.patchset_name):
            print "head exists: "+self.patchset_name
            exit(1)
        root_name = repo.active_branch
        root_commit = repo.head.commit
        patchset = PatchSet()
        patchset.root_name = root_name
        patchset.root_commit = root_commit.id
        work_checkout = GitHiddenCheckout(repo, self.patchset_name)
        work_checkout.file_put_contents( "branches", to_YAML(patchset) )
        work_checkout.add("branches")
        work_checkout.commit("initial commit")

class AddCommand(object):
    def main( self, argv ):
        self.parse(argv)
        self.run()

    def getParser( self ):
        parser = OptionParser()
        return parser

    def parse( self, argv ):
        parser = self.getParser()
        (options, args) = parser.parse_args(args = argv)
        if len(args) != 1:
            print "fail"
            parser.error("")

        self.patchset_name = args[0]

    def run( self ):
        repo = git.Repo(os.getcwd())
        if not git_has_head(repo, self.patchset_name):
            print "patchset does not exists: "+self.patchset_name
            exit(1)

        branch_name = repo.active_branch
        branch_commit = repo.head.commit
        #TODO Check, that patchset's root is an ancestor

        patchset = PatchSet.from_git_tree(repo.tree(self.patchset_name))

        #TODO dependencies from command line
        dependencies = []
        patchset.add_branch( branch_name, PatchBranch(branch_commit.id, dependencies) )

        work_checkout = GitHiddenCheckout(repo, self.patchset_name)
        work_checkout.file_put_contents( "branches", to_YAML(patchset) )
        work_checkout.add("branches")

        #TODO support / in branch_name
        message_file_name = "message_"+urllib.quote_plus(branch_name)

        work_checkout.file_put_contents(message_file_name,"Provide a description!")
        work_checkout.edit_file(message_file_name)
        work_checkout.add(message_file_name)

        work_checkout.commit("added branch: "+branch_name)

class StatusCommand(object):
    def main( self, argv ):
        self.parse(argv)
        self.run()

    def getParser( self ):
        parser = OptionParser()
        return parser

    def parse( self, argv ):
        parser = self.getParser()
        (options, args) = parser.parse_args(args = argv)
        if len(args) != 1:
            print "fail"
            parser.error("")

        self.patchset_name = args[0]

    def run( self ):
        repo = git.Repo(os.getcwd())
        heads_map = git_heads_map(repo)

        if not git_has_head(repo, self.patchset_name):
            print "patchset does not exists: "+self.patchset_name
            exit(1)

        branch_name = repo.active_branch
        branch_commit = repo.commits( start=branch_name, max_count=1 )[0].id
        #TODO Check, that patchset's root is an ancestor

        patchset = PatchSet.from_git_tree(repo.tree(self.patchset_name))
        print "root name: " + patchset.root_name
        print
        print "branches:"
        for branch_name in patchset.branches:
            print "  " + branch_name

class ExportCommand(object):
    def main( self, argv ):
        self.parse(argv)
        self.run()

    def getParser( self ):
        parser = OptionParser()
        return parser

    def parse( self, argv ):
        parser = self.getParser()
        (options, args) = parser.parse_args(args = argv)
        if len(args) != 2:
            print "fail"
            parser.error("")

        self.patchset_name = args[0]
        self.target_dir    = args[1]

    def run( self ):
        repo = git.Repo(os.getcwd())
        if not git_has_head(repo, self.patchset_name):
            print "patchset does not exists: "+self.patchset_name
            exit(1)

        # create dir if it does not exist
        self.makedirs_ignore(self.target_dir)

        # check that dir is empty
        if len(os.listdir(self.target_dir)) > 0:
            print "target dir is not empty: "+self.target_dir
            exit(1)
            
        fp_series = open(os.path.join(self.target_dir,"series"),"w")

        patchset_tree = repo.tree(self.patchset_name)
        patchset = PatchSet.from_git_tree(patchset_tree)
        for branch_name in patchset.branches:
            branch = patchset.branches[branch_name]
            fp_series.write(branch_name+"\n")
            # By now, patches are taken from patchset root
            message_file_name = "message_"+urllib.quote_plus(branch_name)
            patch_content = patchset_tree[message_file_name].data
            patch_content = patch_content + "\n---\n\n"
            patch_content = patch_content + repo.diff(patchset.root_commit, branch.commit)
            self.file_put_content_with_makedir(os.path.join(self.target_dir,branch_name),patch_content)

        fp_series.close()

    def makedirs_ignore(self,path):
        if(os.path.isdir(path)):
            return
        os.makedirs(path)

    def file_put_content_with_makedir(self, path, content):
        self.makedirs_ignore(os.path.dirname(path))
        f = open(path,"w")
        f.write(content)
        f.close()

def main( argv ):
    if len( argv ) < 2:
        print "no command"
        exit(1)
    commandClass = str.capitalize(argv[1]) + "Command"
    command = globals()[commandClass]()
    command.main( argv[2:] )
