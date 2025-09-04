"""
Shell completion commands for Linearator CLI.

Provides shell completion scripts for bash, zsh, and fish shells.
"""

import click
from rich.console import Console

console = Console()


@click.group()
def completion_group() -> None:
    """Shell completion commands."""
    pass


@completion_group.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
@click.pass_context
def install(ctx: click.Context, shell: str) -> None:
    """
    Install shell completion for the specified shell.

    \b
    Supported shells:
        bash    - Bash shell completion
        zsh     - Zsh shell completion
        fish    - Fish shell completion

    \b
    Examples:
        linear-cli completion install bash    # Install bash completion
        linear-cli completion install zsh     # Install zsh completion
        linear-cli completion install fish    # Install fish completion

    \b
    Installation instructions will be displayed for manual setup.
    """
    console.print(
        f"[bold blue]Installing {shell} completion for Linearator[/bold blue]"
    )

    if shell == "bash":
        console.print(
            """
[bold]Bash Completion Setup:[/bold]

1. Generate completion script:
   [dim]linear-cli completion show bash > ~/.linear-cli-completion.bash[/dim]

2. Add to your ~/.bashrc or ~/.bash_profile:
   [dim]source ~/.linear-cli-completion.bash[/dim]

3. Reload your shell or run:
   [dim]source ~/.bashrc[/dim]
"""
        )

    elif shell == "zsh":
        console.print(
            """
[bold]Zsh Completion Setup:[/bold]

1. Generate completion script:
   [dim]linear-cli completion show zsh > ~/.linear-cli-completion.zsh[/dim]

2. Add to your ~/.zshrc:
   [dim]source ~/.linear-cli-completion.zsh[/dim]

3. Reload your shell or run:
   [dim]source ~/.zshrc[/dim]

Alternative (using compinit):
1. Create completion function:
   [dim]linear-cli completion show zsh > ~/.zsh/completions/_linear-cli[/dim]

2. Add to ~/.zshrc (before compinit):
   [dim]fpath=(~/.zsh/completions $fpath)[/dim]
"""
        )

    elif shell == "fish":
        console.print(
            """
[bold]Fish Completion Setup:[/bold]

1. Create fish completions directory:
   [dim]mkdir -p ~/.config/fish/completions[/dim]

2. Generate completion script:
   [dim]linear-cli completion show fish > ~/.config/fish/completions/linear-cli.fish[/dim]

3. Reload fish:
   [dim]exec fish[/dim]
"""
        )


@completion_group.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
@click.pass_context
def show(ctx: click.Context, shell: str) -> None:
    """
    Show shell completion script for the specified shell.

    Output the completion script that can be saved to a file or sourced directly.

    \b
    Examples:
        linear-cli completion show bash > ~/.linear-cli-completion.bash
        linear-cli completion show zsh > ~/.config/zsh/completions/_linear-cli
        linear-cli completion show fish > ~/.config/fish/completions/linear-cli.fish
    """
    if shell == "bash":
        console.print(generate_bash_completion())
    elif shell == "zsh":
        console.print(generate_zsh_completion())
    elif shell == "fish":
        console.print(generate_fish_completion())


def generate_bash_completion() -> str:
    """Generate bash completion script."""
    return """
# Bash completion for linear-cli
_linear-cli_completion() {
    local IFS=$'\n'
    local response

    # WHY: Dynamic completion strategy with fallback for reliability:
    # Primary: Try dynamic completion service for context-aware suggestions
    # Fallback: Use static completion when dynamic completion service unavailable
    # This approach provides the best user experience when possible while maintaining
    # basic completion functionality even when the dynamic service fails
    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$COMP_CWORD linear-cli-complete 2>/dev/null)

    if [ $? -eq 0 ]; then
        eval $response
    else
        # Fallback to basic completion
        local cur="${COMP_WORDS[COMP_CWORD]}"
        local commands="auth config team issue label search bulk user interactive completion status version"
        local options="--help --version --config-dir --team --output-format --no-color --verbose --debug"

        case "${COMP_WORDS[1]}" in
            auth)
                COMPREPLY=($(compgen -W "login logout status" -- "$cur"))
                ;;
            issue)
                COMPREPLY=($(compgen -W "list create update show delete" -- "$cur"))
                ;;
            search)
                COMPREPLY=($(compgen -W "issues history save list" -- "$cur"))
                ;;
            bulk)
                COMPREPLY=($(compgen -W "update-state assign label" -- "$cur"))
                ;;
            user)
                COMPREPLY=($(compgen -W "list show workload suggest" -- "$cur"))
                ;;
            team)
                COMPREPLY=($(compgen -W "list info" -- "$cur"))
                ;;
            label)
                COMPREPLY=($(compgen -W "list create show" -- "$cur"))
                ;;
            completion)
                COMPREPLY=($(compgen -W "install show" -- "$cur"))
                ;;
            *)
                if [[ $cur == -* ]]; then
                    COMPREPLY=($(compgen -W "$options" -- "$cur"))
                else
                    COMPREPLY=($(compgen -W "$commands" -- "$cur"))
                fi
                ;;
        esac
    fi
}

complete -o bashdefault -o default -F _linear-cli_completion linear-cli
"""


def generate_zsh_completion() -> str:
    """Generate zsh completion script."""
    return """
#compdef linear-cli

_linear-cli() {
    local context curcontext="$curcontext" state line
    _arguments -C \
        '--help[Show help message]' \
        '--version[Show version]' \
        '--config-dir[Configuration directory]:directory:_directories' \
        '--team[Default team]:team:' \
        '--output-format[Output format]:format:(table json yaml)' \
        '--no-color[Disable colored output]' \
        '--verbose[Enable verbose output]' \
        '--debug[Enable debug output]' \
        '1: :_linear-cli_commands' \
        '*: :->args'

    case $state in
    args)
        case $line[1] in
        auth)
            _arguments \
                '1: :(login logout status)'
            ;;
        issue)
            _arguments \
                '1: :(list create update show delete)' \
                '--team[Team]:team:' \
                '--assignee[Assignee]:assignee:' \
                '--state[State]:state:' \
                '--labels[Labels]:labels:' \
                '--priority[Priority]:priority:(0 1 2 3 4)'
            ;;
        search)
            _arguments \
                '1: :(issues history save list)' \
                '--team[Team]:team:' \
                '--assignee[Assignee]:assignee:' \
                '--state[State]:state:' \
                '--labels[Labels]:labels:' \
                '--priority[Priority]:priority:(0 1 2 3 4)'
            ;;
        bulk)
            _arguments \
                '1: :(update-state assign label)' \
                '--query[Search query]:query:' \
                '--team[Team]:team:' \
                '--dry-run[Dry run mode]'
            ;;
        user)
            _arguments \
                '1: :(list show workload suggest)' \
                '--team[Team]:team:'
            ;;
        team)
            _arguments \
                '1: :(list info)'
            ;;
        label)
            _arguments \
                '1: :(list create show)' \
                '--team[Team]:team:'
            ;;
        completion)
            _arguments \
                '1: :(install show)' \
                '2: :(bash zsh fish)'
            ;;
        esac
        ;;
    esac
}

_linear-cli_commands() {
    local commands
    commands=(
        'auth:Authentication commands'
        'config:Configuration management'
        'team:Team management'
        'issue:Issue management'
        'label:Label management'
        'search:Search issues'
        'bulk:Bulk operations'
        'user:User management'
        'interactive:Interactive mode'
        'completion:Shell completion'
        'status:Show status'
        'version:Show version'
    )
    _describe 'commands' commands
}

_linear-cli
"""


def generate_fish_completion() -> str:
    """Generate fish completion script."""
    return """
# Fish completion for linear-cli

# Global options
complete -c linear-cli -l help -d 'Show help message'
complete -c linear-cli -l version -d 'Show version'
complete -c linear-cli -l config-dir -d 'Configuration directory' -r
complete -c linear-cli -l team -d 'Default team' -r
complete -c linear-cli -l output-format -d 'Output format' -x -a 'table json yaml'
complete -c linear-cli -l no-color -d 'Disable colored output'
complete -c linear-cli -l verbose -d 'Enable verbose output'
complete -c linear-cli -l debug -d 'Enable debug output'

# Main commands
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'auth' -d 'Authentication commands'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'config' -d 'Configuration management'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'team' -d 'Team management'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'issue' -d 'Issue management'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'label' -d 'Label management'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'search' -d 'Search issues'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'bulk' -d 'Bulk operations'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'user' -d 'User management'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'interactive' -d 'Interactive mode'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'completion' -d 'Shell completion'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'status' -d 'Show status'
complete -c linear-cli -f -n '__fish_use_subcommand' -a 'version' -d 'Show version'

# Auth subcommands
complete -c linear-cli -f -n '__fish_seen_subcommand_from auth' -a 'login' -d 'Login to Linear'
complete -c linear-cli -f -n '__fish_seen_subcommand_from auth' -a 'logout' -d 'Logout from Linear'
complete -c linear-cli -f -n '__fish_seen_subcommand_from auth' -a 'status' -d 'Show auth status'

# Issue subcommands
complete -c linear-cli -f -n '__fish_seen_subcommand_from issue' -a 'list' -d 'List issues'
complete -c linear-cli -f -n '__fish_seen_subcommand_from issue' -a 'create' -d 'Create issue'
complete -c linear-cli -f -n '__fish_seen_subcommand_from issue' -a 'update' -d 'Update issue'
complete -c linear-cli -f -n '__fish_seen_subcommand_from issue' -a 'show' -d 'Show issue details'
complete -c linear-cli -f -n '__fish_seen_subcommand_from issue' -a 'delete' -d 'Delete issue'

# Issue options
complete -c linear-cli -n '__fish_seen_subcommand_from issue' -l team -d 'Team filter' -r
complete -c linear-cli -n '__fish_seen_subcommand_from issue' -l assignee -d 'Assignee filter' -r
complete -c linear-cli -n '__fish_seen_subcommand_from issue' -l state -d 'State filter' -r
complete -c linear-cli -n '__fish_seen_subcommand_from issue' -l labels -d 'Labels filter' -r
complete -c linear-cli -n '__fish_seen_subcommand_from issue' -l priority -d 'Priority filter' -x -a '0 1 2 3 4'

# Search subcommands
complete -c linear-cli -f -n '__fish_seen_subcommand_from search' -a 'issues' -d 'Search issues'
complete -c linear-cli -f -n '__fish_seen_subcommand_from search' -a 'history' -d 'Search history'
complete -c linear-cli -f -n '__fish_seen_subcommand_from search' -a 'save' -d 'Save search'
complete -c linear-cli -f -n '__fish_seen_subcommand_from search' -a 'list' -d 'List saved searches'

# Bulk subcommands
complete -c linear-cli -f -n '__fish_seen_subcommand_from bulk' -a 'update-state' -d 'Bulk state updates'
complete -c linear-cli -f -n '__fish_seen_subcommand_from bulk' -a 'assign' -d 'Bulk assignments'
complete -c linear-cli -f -n '__fish_seen_subcommand_from bulk' -a 'label' -d 'Bulk labeling'

# User subcommands
complete -c linear-cli -f -n '__fish_seen_subcommand_from user' -a 'list' -d 'List users'
complete -c linear-cli -f -n '__fish_seen_subcommand_from user' -a 'show' -d 'Show user details'
complete -c linear-cli -f -n '__fish_seen_subcommand_from user' -a 'workload' -d 'Workload analysis'
complete -c linear-cli -f -n '__fish_seen_subcommand_from user' -a 'suggest' -d 'Assignment suggestions'

# Team subcommands
complete -c linear-cli -f -n '__fish_seen_subcommand_from team' -a 'list' -d 'List teams'
complete -c linear-cli -f -n '__fish_seen_subcommand_from team' -a 'info' -d 'Show team info'

# Label subcommands
complete -c linear-cli -f -n '__fish_seen_subcommand_from label' -a 'list' -d 'List labels'
complete -c linear-cli -f -n '__fish_seen_subcommand_from label' -a 'create' -d 'Create label'
complete -c linear-cli -f -n '__fish_seen_subcommand_from label' -a 'show' -d 'Show label details'

# Completion subcommands
complete -c linear-cli -f -n '__fish_seen_subcommand_from completion' -a 'install' -d 'Install completion'
complete -c linear-cli -f -n '__fish_seen_subcommand_from completion' -a 'show' -d 'Show completion script'
complete -c linear-cli -f -n '__fish_seen_subcommand_from completion; and __fish_seen_subcommand_from install show' -a 'bash zsh fish'
"""


# Standalone completion command (alternative to group)
@click.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
@click.pass_context
def completion(ctx: click.Context, shell: str) -> None:
    """
    Generate shell completion script.

    This is a convenient alias for 'completion show'.
    """
    ctx.invoke(show, shell=shell)
