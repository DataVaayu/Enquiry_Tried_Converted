echo off

echo "This is a garbage text file">garbagetxtfile.txt

call git_code_updater

del garbagetxtfile.txt

call git_code_updater