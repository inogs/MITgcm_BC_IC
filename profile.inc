MIT_DAYS=10

function mit_days {

for (( days=0; days<$MIT_DAYS ; days++ )) ; do
   date -d "$DATESTART + $days days" +%Y%m%d
done
}

function weekly_linker {

sourcefile=$1
AVE_DAILY_DIR=$2
var=${sourcefile:${#sourcefile}-6:3}


if ! [ -f $sourcefile ] ; then
 echo "$sourcefile not found"
 return 1
fi

for D in `mit_days` ; do
   ln -fs ${sourcefile} $AVE_DAILY_DIR/ave.${D}-12:00:00.${var}.nc
done

}

function medmit_prex_or_die {
  # Like medmit_prex, but in case of failure runs medmit_die
  typeset _command="$1"
  shift 1
  medmit_prex "$_command" || {
    typeset -i _ec=${1:-1}
    typeset    _message="${2:-Command '$_command' failed}"
    medmit_die "$_ec" "$_message"
  }
}


function medmit_date {
 date
}

function medmit_prex {
  # PRint a command and EXecutes it;
  # after the command has been executed, medmit_prex prints its exit_code and returns the same value
  typeset -i _ec
  printf "PrEx $(medmit_date)    > %s\n" "$*"
  _logical_sim="${2:-false}"

  if $_logical_sim ; then
    echo "[WRN: CMD SIMULATED]:: $1" ; _ec=$?
  else
    eval "$1" ; _ec=$?
  fi
  typeset _status
  if [[ $_ec -eq 0 ]] ; then
    _status="ok"
  else
    _status="KO"
  fi
  printf "PrEx $(medmit_date) %3d< %s [%s]\n" "$_ec" "$*" "$_status"
  return $_ec
}

function medmit_die {
  # log an error message and die
  typeset -i _ec="$1"
  shift 1
  medmit_log 0 "$@"
  medmit_exit $_ec
}

function medmit_log {
  # Write a log messages ($2...) on standard output;
  # is $1 is lower than $medmit_LOGMAX, the messages is written also onto $medmit_LOGFILE
  if [[ $medmit_LOGMAX -eq $medmit_DISABLE_LOG ]] ; then
    return 0
  fi
  typeset -i _nlog="$1"
  shift 1
  for _message in "$@" ; do
    if ( $medmit_BATCH ) && [[ $medmit_LOGMAX -ne $medmit_DISABLE_LOG_ON_LOGFILE && $_nlog -le $medmit_LOGMAX ]] ; then
      printf '%s %02d (%s) : %s\n' "$(medmit_date)" "$_nlog" "$medmit_RUNID" "$_message" | tee -a $medmit_LOGFILE
    else
      printf '%s %02d (%s) : %s\n' "$(medmit_date)" "$_nlog" "$medmit_RUNID" "$_message"
    fi
  done
}

function medmit_exit {
  # Log message for script exit
  typeset -i _default_ec=${_medmit_EXIT_CODE:-$?}
  typeset -i _ec=${1:-$_default_ec}
  #echo "medmit_exit(${1}->${_default_ec}->${_ec})"
  typeset    _message=""
  if [[ "$1" == "" ]] ; then
    _message=" (from last executed command)"
  fi
  if $_medmit_START_DONE && ! $_medmit_EXIT_DONE ; then
    medmit_log 0 "* EXIT(${medmit_PROGNAME}) [$(medmit_exitcode ${_ec})]$_message"
    _medmit_EXIT_DONE=true
    _medmit_EXIT_CODE=${_ec}
  fi
  exit $_ec
}

function medmit_linker {

for I in `ls $1 `; do
   ln -fs $I
done
}

