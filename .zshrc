# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH

# Path to your oh-my-zsh installation.
  export ZSH="/home/johnny/.oh-my-zsh"

# Opciones de Zsh
unsetopt MENU_COMPLETE                                      # NO autoseleccionar la primera autocompletación
unsetopt FLOW_CONTROL                                       # Desactivar inicio/parada de caracteres en el editor del shell
unsetopt NO_BEEP                                            # Se escuchan los beeps de error

setopt AUTO_CD                                              # Se mueve al directorio que coincida
setopt ALWAYS_TO_END                                        # Mover el cursor al final de la palabra
setopt AUTO_MENU                                            # Muestra el menú de completación en sucesivos tabs
setopt AUTO_NAME_DIRS                                       # Los parámetros que se establecen con el nombre absoluto de un directorio se convierten inmediatamente en un nombre para ese directorio
setopt AUTO_LIST                                            # Automáticamente muestras las opciones en completaciones ambiguas
setopt AUTO_PARAM_SLASH                                     # Agrega un slash si el parámetro completo es un directorio

setopt COMPLETE_IN_WORD                                     # Permitir la finalización desde dentro de una palabra/frase
setopt CORRECT                                              # Intenta corregir los comandos
setopt PATH_DIRS                                            # Busca en el PATH para completar las palabras

setopt APPEND_HISTORY                                       # Agrega historial
setopt EXTENDED_HISTORY                                     # Agrega timestamps al historial
setopt INC_APPEND_HISTORY                                   # Historial incremental
setopt HIST_EXPIRE_DUPS_FIRST                               # Se eliminan primero los duplicados más viejosfirst
setopt HIST_IGNORE_ALL_DUPS                                 # NO almacenar duplicados
setopt HIST_IGNORE_SPACE                                    # Elimina del historial los comandos que empiecen con un espacio
setopt HIST_FIND_NO_DUPS                                    # NO muestra los comandos duplicados
setopt HIST_REDUCE_BLANKS                                   # Elimina los espacios en blanco en los comandos guardados
setopt HIST_VERIFY                                          # NO ejecuta el comando, sólo lo muestra
setopt SHARE_HISTORY                                        # Historial compartido entre sesiones

ZSH_THEME="powerlevel9k/powerlevel9k"

# Configuraciones para PowerLevel9K
POWERLEVEL9K_MODE='nerdfont-complete'
POWERLEVEL9K_PROMPT_ON_NEWLINE=true
POWERLEVEL9K_PROMPT_ADD_NEWLINE=true

# Colores para el segmento de Contexto (username@host) de PowerLevel9K
POWERLEVEL9K_CONTEXT_DEFAULT_FOREGROUND="220"
POWERLEVEL9K_CONTEXT_DEFAULT_BACKGROUND="236"
POWERLEVEL9K_CONTEXT_ROOT_FOREGROUND="0"
POWERLEVEL9K_CONTEXT_ROOT_BACKGROUND="202"
POWERLEVEL9K_CONTEXT_REMOTE_FOREGROUND="11"
POWERLEVEL9K_CONTEXT_REMOTE_BACKGROUND="1"

# Colores para los segmentos de directorio de PowerLevel9K
POWERLEVEL9K_DIR_HOME_FOREGROUND="24"
POWERLEVEL9K_DIR_HOME_BACKGROUND="220"
POWERLEVEL9K_DIR_HOME_SUBFOLDER_FOREGROUND="220"
POWERLEVEL9K_DIR_HOME_SUBFOLDER_BACKGROUND="24"
POWERLEVEL9K_DIR_DEFAULT_FOREGROUND="0"
POWERLEVEL9K_DIR_DEFAULT_BACKGROUND="246"

# Colores para el segmento de escritura de directorio de PowerLevel9K
POWERLEVEL9K_DIR_WRITABLE_FORBIDDEN_FOREGROUND="226"
POWERLEVEL9K_DIR_WRITABLE_FORBIDDEN_BACKGROUND="1"

# Sementos configurados en los PROMPT de PowerLevel9K
POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=(context dir_writable dir rbenv vcs newline status)
POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(status root_indicator background_jobs history time)

# prompt JavaScript
POWERLEVEL9K_CUSTOM_JAVASCRIPT="echo -n '\ue781' JavaScript"
POWERLEVEL9K_CUSTOM_JAVASCRIPT_FOREGROUND="black"
POWERLEVEL9K_CUSTOM_JAVASCRIPT_BACKGROUND="yellow"

POWERLEVEL9K_CUSTOM_PYTHON="echo -n '\uf81f' Python"
POWERLEVEL9K_CUSTOM_PYTHON_FOREGROUND="black"
POWERLEVEL9K_CUSTOM_PYTHON_BACKGROUND="blue"

POWERLEVEL9K_CUSTOM_RUBY="echo -n '\ue21e' Ruby"
POWERLEVEL9K_CUSTOM_RUBY_FOREGROUND="black"
POWERLEVEL9K_CUSTOM_RUBY_BACKGROUND="red"

# Soporte de 256 colores para la cónsola
TERM=xterm-256color

# Uncomment the following line if you want to change the command execution time
# stamp shown in the history command output.
# You can set one of the optional three formats:
# "mm/dd/yyyy"|"dd.mm.yyyy"|"yyyy-mm-dd"
# or set a custom format using the strftime function format specifications,
# see 'man strftime' for details.
HIST_STAMPS="mm/dd/yyyy"

# Would you like to use another custom folder than $ZSH/custom?
# ZSH_CUSTOM=/path/to/new-custom-folder

# Which plugins would you like to load?
# Standard plugins can be found in ~/.oh-my-zsh/plugins/*
# Custom plugins may be added to ~/.oh-my-zsh/custom/plugins/
# Example format: plugins=(rails git textmate ruby lighthouse)
# Add wisely, as too many plugins slow down shell startup.
plugins=(
  git
)

source $ZSH/oh-my-zsh.sh

# User configuration

# export MANPATH="/usr/local/man:$MANPATH"

# You may need to manually set your language environment
export LANG=es_PE.UTF-8

# Preferred editor for local and remote sessions
if [[ -n $SSH_CONNECTION ]]; then
	export EDITOR='nano'
else
	export EDITOR='mvim'
fi

# Verificación de actualizaciones cada 15 días
export UPDATE_ZSH_DAYS=15

# Sensible a mayúsculas
CASE_SENSITIVE="true"                               

autoload colors
colors
export LS_COLORS='no=00:fi=00:di=00;34:ln=00;36:pi=40;33:so=00;35:bd=40;33;01:cd=40;33;01:or=01;05;37;41:mi=01;05;37;41:ex=00;35:*.cmd=00;32:*.exe=00;32:*.sh=00;32:*.gz=00;31:*.bz2=00;31:*.bz=00;31:*.tz=00;31:*.rpm=00;31:*.cpio=00;31:*.t=93:*.pm=00;36:*.pod=00;96:*.conf=00;33:*.off=00;9:*.jpg=00;94:*.png=00;94:*.xcf=00;94:*.JPG=00;94:*.gif=00;94:*.pdf=00;91'
export GIT_EDITOR=$EDITOR

# Compilation flags
# export ARCHFLAGS="-arch x86_64"

# ssh
# export SSH_KEY_PATH="~/.ssh/rsa_id"

# Set personal aliases, overriding those provided by oh-my-zsh libs,
# plugins, and themes. Aliases can be placed here, though oh-my-zsh
# users are encouraged to define aliases within the ZSH_CUSTOM folder.
# For a full list of active aliases, run `alias`.
#
# Example aliases
# alias zshconfig="mate ~/.zshrc"
# alias ohmyzsh="mate ~/.oh-my-zsh"
