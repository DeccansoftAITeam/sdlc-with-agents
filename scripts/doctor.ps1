# Checks the course toolbox. Prints one line per tool.
foreach ($c in 'git','gh','python','uv','node','pnpm','docker','az','claude','code') {
    if (Get-Command $c -ErrorAction SilentlyContinue) {
        $v = (& $c --version 2>$null | Where-Object { $_ -notmatch 'WARNING' } | Select-Object -First 1)
        '{0,-8} {1}' -f $c, $v
    } else {
        '{0,-8} MISSING' -f $c
    }
}
