# Experiment 10: Kubernetes Deployment & Load Simulation (Minikube Version)
**Course:** Distributed Computing Lab (DC Lab)  
**Project Integration:** ResearchPilot AI

---

## 1. Experiment Overview & Objective

| Parameter | Details |
|---|---|
| **Experiment No.** | 10 |
| **Title** | Deploy a Complete System on Kubernetes + Simulate Load |
| **Goal** | Take the `ResearchWorkerService`, containerize it, deploy a 3-node cluster inside **Minikube**, and verify that gRPC traffic is properly load-balanced across the pods. |
| **Why Kubernetes?** | Kubernetes self-heals (restarts crashed pods automatically). We are also demonstrating the **"gRPC Trap Fix"** by using a Headless Service and `dns:///` resolution to force true load balancing across gRPC connections. |

---

## 2. Step-by-Step Execution Guide (With Screenshot Checkpoints)

*Ensure you have Docker Desktop running in the background and `minikube` installed.*

Open **Git Bash** and navigate to your experiment folder:
```bash
cd C:/Users/bharg/researchpilot-ai/grpc_experiment
```

### Step 1: Start Minikube
Run the following command to boot up your local Kubernetes cluster:
```bash
minikube start
```
> 📸 **SCREENSHOT 1:** Take a screenshot of the terminal once it says "Done! kubectl is now configured to use minikube".

### Step 2: Point Docker to Minikube
Because Minikube runs its own isolated Docker environment inside a VM, you must point your terminal to it so your built image goes into Minikube's registry (otherwise K8s won't be able to find the image!)
```bash
eval $(minikube docker-env)
```
*(Note: This command produces no output, which is normal).*

### Step 3: Build the Docker Image
Now, build the container image inside the Minikube environment:
```bash
docker build -t myapp-backend:latest .
```
> 📸 **SCREENSHOT 2:** Take a screenshot of the final build step showing "Successfully tagged myapp-backend:latest".

### Step 4: Deploy the Cluster
Tell Kubernetes to spin up your 3-node cluster using the manifest files I created for you:
```bash
kubectl apply -f k8s/app.yaml
```
> 📸 **SCREENSHOT 3:** Take a screenshot showing "deployment.apps/research-worker created" and "service/worker-svc created".

Verify they are running (you may have to run this twice until they all say `Running`):
```bash
kubectl get pods
```
> 📸 **SCREENSHOT 4:** Take a screenshot showing all 3 `research-worker-xxxxx` pods in the `Running` state with 0 restarts.

### Step 5: Run the Load Test
Fire 20 concurrent gRPC requests at the cluster by deploying the test job:
```bash
kubectl apply -f k8s/load-test-job.yaml
```
Wait a few seconds for the job to finish executing:
```bash
kubectl wait --for=condition=complete job/load-test --timeout=90s
```

### Step 6: Verify the Load Balancing!
Read the logs from the load test client to see which nodes processed the 20 requests:
```bash
kubectl logs job/load-test
```
> 📸 **SCREENSHOT 5:** Take a screenshot of the output. **This is the most important screenshot for your lab report!** It proves that requests were randomly distributed across different pods (thanks to the Headless Service and `round_robin` policy) rather than 100% of the traffic hitting just one node!

### Step 7: Test Kubernetes Self-Healing (Failover)
Let's see what happens if a node crashes! Run `kubectl get pods` and copy the exact name of one of your worker pods.

Delete it manually to simulate a crash:
```bash
kubectl delete pod <PASTE-YOUR-POD-NAME-HERE>
```

Check the pods again immediately:
```bash
kubectl get pods
```
> 📸 **SCREENSHOT 6:** Take a screenshot showing your deleted pod `Terminating` and a brand new pod `ContainerCreating` or `Running`. This proves Kubernetes immediately detected the missing node and spun up a replacement to maintain the 3-node contract!

### Step 8: Clean Up
When your documentation is complete, tear down the deployment and stop Minikube:
```bash
kubectl delete -f k8s/app.yaml
kubectl delete -f k8s/load-test-job.yaml
minikube stop
```
