FROM registry-vpc.cn-beijing.aliyuncs.com/benepal/kido-env:20250724

WORKDIR /code/src

COPY requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir -r /code/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

COPY ./src /code/src
COPY ./cert /code/cert
COPY ./apiclient_cert.pem /code/apiclient_cert.pem
COPY ./apiclient_key.pem /code/apiclient_key.pem

ENV PYTHONPATH "${PYTHONPATH}:/code/src"

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80", "--log-level=info", "--timeout-keep-alive=5", "--limit-concurrency=1000", "--backlog=2048"]
