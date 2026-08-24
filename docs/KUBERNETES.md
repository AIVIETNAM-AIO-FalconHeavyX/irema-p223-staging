# Hướng Dẫn Triển Khai Kubernetes & Cloud Native Cho P223 Backend

Tài liệu này hướng dẫn chi tiết cách cấu hình Pod, Liveness / Readiness Probes, Horizontal Pod Autoscaler (HPA) và quản lý tài nguyên bộ nhớ cho hệ thống FastAPI + RAG Model.

---

## 1. Nguyên Lý Thiết Kế Health Probes

Hệ thống cung cấp 2 loại Probes tiêu chuẩn phục vụ Kubernetes:

| Probe | Endpoint | Mục Đích | Kỳ Vọng K8s |
|---|---|---|---|
| **Liveness Probe** | `/live` (hoặc `/health/live`) | Xác định tiến trình Uvicorn có bị chết/treo cứng event loop hay không. | Luôn trả về `200 OK`. Nếu fail $\rightarrow$ K8s **Restart Pod**. |
| **Readiness Probe** | `/ready` (hoặc `/health/ready`) | Xác định RAG Models và MinIO S3 Sync đã sẵn sàng phục vụ hay chưa. | Trả về `503` khi đang nạp; trả `200 OK` khi sẵn sàng. Nếu fail $\rightarrow$ K8s **Chưa điều hướng Traffic** vào Pod (không restart). |
| **General Health** | `/health` | Phục vụ Frontend / Monitor Dashboard. | Trả về JSON sub-status chi tiết. |

---

## 2. Kubernetes Deployment Manifest Mẫu (`backend-deployment.yaml`)

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: p223-backend
  namespace: default
  labels:
    app: p223-backend
spec:
  replicas: 2 # Scale theo chiều ngang (Horizontal Pods)
  selector:
    matchLabels:
      app: p223-backend
  template:
    metadata:
      labels:
        app: p223-backend
    spec:
      containers:
        - name: backend
          image: p223-backend:latest
          imagePullPolicy: IfNotPresent
          command: ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
          ports:
            - containerPort: 8000
              name: http
          envFrom:
            - configMapRef:
                name: p223-config
            - secretRef:
                name: p223-secrets
          resources:
            requests:
              cpu: "1000m"
              memory: "2Gi"
            limits:
              cpu: "2000m"
              memory: "4Gi"
          # -------------------------------------------------------------
          # 1. Liveness Probe: Kiểm tra sống còn sau 5 giây boot
          # -------------------------------------------------------------
          livenessProbe:
            httpGet:
              path: /live
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
            timeoutSeconds: 3
            failureThreshold: 3

          # -------------------------------------------------------------
          # 2. Readiness Probe: Chờ RAG model nạp xong mới route traffic
          # -------------------------------------------------------------
          readinessProbe:
            httpGet:
              path: /ready
              port: http
            initialDelaySeconds: 15
            periodSeconds: 5
            timeoutSeconds: 3
            failureThreshold: 6
```

---

## 3. Horizontal Pod Autoscaler (HPA)

Vì mỗi container chạy `--workers 1` để tối ưu bộ nhớ cho SentenceTransformer / CrossEncoder, việc mở rộng khả năng phục vụ được thực hiện thông qua HPA:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: p223-backend-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: p223-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
```

---

## 4. Kiểm Tra Thử Nghiệm

### Kiểm tra Liveness (Ngay khi vừa bật container):
```bash
curl -i http://localhost:8000/live
# HTTP/1.1 200 OK
# {"status":"alive","service":"VF AI Onboarding Agent","env":"development", ...}
```

### Kiểm tra Readiness (Trong 10-15s đầu lúc model đang tải ngầm):
```bash
curl -i http://localhost:8000/ready
# HTTP/1.1 503 Service Unavailable
# {"status":"unready","rag_ready":false,"s3_ready":false,"env":"development"}
```

### Kiểm tra Readiness (Sau khi model và S3 đã sẵn sàng):
```bash
curl -i http://localhost:8000/ready
# HTTP/1.1 200 OK
# {"status":"ready","rag_ready":true,"s3_ready":true,"env":"development"}
```
