# Keep an open question waiting for the user

Apply this lifecycle to first-use choices, missing intake fields and an agreed
collaboration checkpoint. It governs question handling, not app UI configuration.
Reuse existing answers and the current brief; do not add another approval step.

## Display and wait

1. Prefer a supported blocking question control when it is available and allowed
   in the current mode. Otherwise use the host's asynchronous question control.
   Keep the existing limit of at most three concise grouped questions. Follow
   the tool's actual schema and restrictions; do not switch modes just to ask.
2. An acknowledgment such as `accepted: true` means the question was displayed.
   It does not contain a user answer. A suggested or preselected option also
   stays unanswered until the user submits it.
3. After displaying an asynchronous question, continue only work independent of
   its answer. Keep the question open. Do not send a final message, summarize
   the unanswered choices, or declare the request complete while that control
   is still waiting for input. A final message ends the active turn and can
   interrupt the host's input flow.
4. When independent work is exhausted, use an available wait/sleep tool that
   yields on new user input. Keep each blocking wait call at 60 seconds or less
   so new input and host limits can be handled. Repeat waits as needed until a
   submitted answer, explicit cancellation, or a real host limitation arrives.
   A wait timeout is only a chance to check for input, not the end of the
   question. Do not use short busy polling or repeatedly repost the questions.
5. Give the user time to read and type. As a review checkpoint, allow at least
   60 seconds for a simple choice and at least three minutes for a bundled or
   free-text answer, unless a reply arrives sooner. These are minimum waiting
   guidelines, never automatic deadlines. After them, continue waiting while
   the control is open. Never infer typing status that the host does not expose.

## Apply a reply

Use the submitted reply directly. Preserve its resolved choices and leave other
fields pending. Ask only the remainder when needed; do not repeat the whole
intake. A side question or status request does not dismiss an open question:
answer briefly in commentary and resume the pending work or wait. An explicit
user cancellation, change of task, or request to use ordinary chat takes
precedence; keep any relevant resolved choices for later reuse.

Elapsed time, silence, a display acknowledgment and a wait timeout never mean
approval, delegation, completion or adoption of recommendations. Do not start
answer-dependent writing, design or export until the required choices resolve.

## When the host cannot retain the question control

If no compatible question/wait tool is available, the host explicitly dismisses
or expires the question, or a host limit prevents further waiting, preserve the
answered and unanswered fields. Briefly explain the actual limitation and show
only the remaining questions as ordinary chat text. The user can submit them
in a later message. Do not claim that the input was saved, that an app timeout
was changed, or that the user selected a default. Do not repeatedly reopen a
failed control without a reason.

A normal chat message containing questions may end its turn when no interactive
control is open. The prohibition above applies to ending a turn while an
interactive question control is still awaiting input.

## Verification boundary

Source checks and intake regressions verify the instructions and pending-choice
preservation. They do not prove that a particular host keeps its UI or typed
draft open. Check the installed update in that host before claiming the input
flow is fixed. Do not create an extra chat or ask the user to type a test answer
without authorization merely to validate this instruction update.
