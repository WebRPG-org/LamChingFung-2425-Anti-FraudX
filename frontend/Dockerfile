FROM nginx:alpine

# 複製前端文件到 nginx
COPY . /usr/share/nginx/html/

# 複製 nginx 配置
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]

