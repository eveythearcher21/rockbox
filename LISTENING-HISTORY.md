# Local listening-history export, version 1

The Database → spotify wrapped screen reads `.rockbox/listening-history-v1.tsv`. This is an append-only, UTF-8, tab-separated journal; it is also the export for a future sync app. No network request, Spotify account integration, or Spotify import occurs. The updater does not ship a journal or overwrite an existing one.

## Recording and rankings

Enable Gather Runtime Data, index your music in the database, and set the player's date/time. The recorder uses Rockbox's existing runtime-data eligibility: a completed/automatically advanced track, or a manual interruption after at least 15 seconds, with nonzero elapsed time and a matching database entry. Pausing does not complete a play. The event appears when the track ends or changes, not when it starts. Repeating a track produces separate qualifying events.

The timestamp is the device-local completion/change time, without timezone or UTC conversion. A track spanning midnight belongs to the month in which its event is recorded. Invalid clocks, write failures or lack of storage can prevent recording; the UI warns about failures detected during the current session. This update cannot reconstruct prior months from existing lifetime play counts. Changing the clock can affect future month/year assignment.

Songs are identified by their full stored path. Renaming/moving a file creates a new identity; identical titles at different paths remain separate. Monthly views count events in the selected calendar month; yearly views aggregate the selected year and display its top song. Equal play counts use the first matching journal event as a deterministic tie breaker. The UI shows up to ten songs; shorter months show the available songs. It supports up to 2,400 distinct months and a bounded ranking table; resource limits are reported rather than silently returning partial rankings.

## Wire format

The first line is exactly `# rockbox-listening-history<TAB>1<LF>`. Every event has seven fields, in this order:

1. Local timestamp: `YYYY-MM-DDThh:mm:ss`.
2. Elapsed milliseconds, unsigned decimal.
3. Track length milliseconds, unsigned decimal.
4. Full device path.
5. Song title.
6. Artist.
7. Album.

Fields are separated by literal tab bytes and rows end with a literal newline. Inside text fields, backslash, tab, newline and carriage return are encoded as `\\`, `\t`, `\n`, and `\r`. Decode those escapes after splitting fields. Metadata can be empty; each tag is capped at 512 UTF-8 bytes at a character boundary. UI labels are shorter. Paths must fit Rockbox's 260-byte path buffer. Do not treat escaped tabs as separators or apply generic CSV quoting rules.

For example (shown with `<TAB>` separators for readability):

```text
# rockbox-listening-history<TAB>1
2026-10-27T14:05:03<TAB>180000<TAB>180000<TAB>/Music/Artist/Track.flac<TAB>Track<TAB>Artist<TAB>Album
```

## Sync-app reader contract

Copy the journal after safely stopping/ejecting the player, or read a stable snapshot. Verify the header, split complete newline-terminated rows, validate the seven fields, then decode text escapes. Ignore an incomplete final row and retry it on the next read. The device writer can truncate an interrupted final append before recording another event; unknown file headers are never rewritten. Readers should tolerate malformed rows without attributing them to a month.

For incremental imports, retain the source device identity supplied by your sync app, a file-generation identifier you manage, and the byte offset of each complete event. A timestamp is not a unique key: multiple events can share a second. Import `(device, generation, byte offset)` once, detect truncation/replacement and start a new generation. Do not rewrite this file from the sync app while Rockbox is running. Back it up with the player's other data. Metadata and paths are local personal library information; uploading or converting them should be an explicit sync-app action.
