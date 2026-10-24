# Immutable Inbox archive whitespace exception

The exact old live Inbox is133518bytes, Git blob9a242456d493f60d30298e7a4047a5e5fb5d4ceb. Its inherited extra blank line at EOF makes git diff --check report new blank line at EOF when adding the archive as a new file. Project governance requires byte-for-byte immutable archival, so no whitespace was stripped. All remaining staged files pass git diff --cached --check with only this exact archive path excluded. Original-to-archive byte equality was independently asserted before staging; this is not a source/test formatting exception.
