ARG FUNCTION_DIR="/function"

FROM python:3.13 AS build-image

ARG FUNCTION_DIR
RUN mkdir -p ${FUNCTION_DIR}
COPY handler.py ${FUNCTION_DIR}

RUN pip install --target ${FUNCTION_DIR} awslambdaric

FROM dhi.io/python:3.13

ARG FUNCTION_DIR
WORKDIR ${FUNCTION_DIR}

COPY --from=build-image ${FUNCTION_DIR} ${FUNCTION_DIR}

ENTRYPOINT [ "/opt/python/bin/python", "-m", "awslambdaric" ]
CMD [ "handler.handler" ]
