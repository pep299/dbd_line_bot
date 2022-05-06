FROM public.ecr.aws/lambda/python:3.9

COPY . .

RUN pip install -r requirements.txt

CMD [ "lambda_function.lambda_handler" ]
