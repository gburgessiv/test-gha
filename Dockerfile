FROM debian:stable-slim
LABEL maintainer="George Burgess <george.burgess.iv@gmail.com>"

# Grab the packages
RUN apt-get update
RUN apt-get install -y python3 python3-requests python3-yaml

ENV LANG=C.UTF-8

# Rootn't
RUN \
  useradd email-bot && \
  mkdir /home/email-bot && \
  chown email-bot:email-bot /home/email-bot

USER email-bot
WORKDIR /home/email-bot

CMD ["bash", "-c", "cd llvm-security-repo && . secrets && exec ./email_about_issues.py --state-file=state.json --debug"]
