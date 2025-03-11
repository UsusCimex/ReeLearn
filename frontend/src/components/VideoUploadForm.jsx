// src/components/VideoUploadForm.jsx
import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  TextField,
  Button,
  LinearProgress,
  Typography,
  Paper,
  Snackbar,
  Alert,
  Grid,
  Tooltip,
  IconButton,
  Chip,
  Divider
} from "@mui/material";
import AlertMessage from "./AlertMessage";
import { uploadVideo, getTaskStatus, checkServerHealth, cleanupTempFiles } from "../services/api";
import { useTranslation } from "../hooks/useTranslation";
import StorageIcon from '@mui/icons-material/Storage';
import DeleteSweepIcon from '@mui/icons-material/DeleteSweep';
import CheckIcon from '@mui/icons-material/Check';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import { formatFileSize } from "../utils/formatters";

const VideoUploadForm = () => {
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [taskId, setTaskId] = useState("");
  const [progress, setProgress] = useState(0);
  const [statusText, setStatusText] = useState("");
  const [error, setError] = useState("");
  const [uploadWarning, setUploadWarning] = useState("");
  const [serverInfo, setServerInfo] = useState(null);
  const [checkingServer, setCheckingServer] = useState(false);
  const [cleaning, setCleaning] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  const { t } = useTranslation();
  const fileInputRef = useRef();
  const uploadInProgress = useRef(false);

  // Проверяем состояние сервера при загрузке компонента
  useEffect(() => {
    checkServerStatus();
  }, []);

  const checkServerStatus = async () => {
    try {
      setCheckingServer(true);
      const health = await checkServerHealth();
      setServerInfo(health);
      
      // Если место на диске ниже критического, предупреждаем пользователя
      if (health.disk_space_warning) {
        setUploadWarning(
          t("lowServerDiskSpace", 
            "Warning: Low disk space on the server. Large uploads may fail.")
        );
      }
    } catch (error) {
      console.error("Error checking server health:", error);
      setUploadWarning(
        t("serverCheckFailed", 
          "Could not verify server status. Upload may be limited.")
      );
    } finally {
      setCheckingServer(false);
    }
  };

  const handleCleanupTempFiles = async () => {
    try {
      setCleaning(true);
      const result = await cleanupTempFiles(true); // force = true для удаления всех временных файлов
      
      if (result && result.space_freed_mb) {
        setServerInfo(prev => {
          if (!prev) return prev;
          
          const freedBytes = result.space_freed_mb * 1024 * 1024;
          return {
            ...prev,
            system: {
              ...prev.system,
              disk: {
                ...prev.system.disk,
                free: prev.system.disk.free + freedBytes,
                free_gb: (prev.system.disk.free + freedBytes) / (1024**3),
                free_percent: ((prev.system.disk.free + freedBytes) * 100) / prev.system.disk.total
              }
            },
            temp_files: {
              ...prev.temp_files,
              count: 0,
              total_size_mb: 0
            }
          };
        });
        
        // Показываем сообщение об успешной очистке
        setUploadWarning(
          t("cleanupSuccess", 
            `Successfully cleaned up server space. Freed ${result.space_freed_mb.toFixed(1)} MB`)
        );
      }
      
      // Обновляем информацию о сервере
      checkServerStatus();
    } catch (error) {
      console.error("Error cleaning up temp files:", error);
      setError(t("cleanupFailed", "Failed to clean up temporary files."));
    } finally {
      setCleaning(false);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) {
      setError(t("pleaseSelectFile", "Please select a video file."));
      return;
    }
    
    // Проверка размера файла перед загрузкой
    if (file.size > 15 * 1024 * 1024 * 1024) { // 15 ГБ
      setError(t("fileTooLarge", "File size exceeds the maximum allowed (15 GB)."));
      return;
    }
    
    try {
      // Предотвращаем повторную загрузку
      if (uploadInProgress.current) {
        setUploadWarning(t("uploadInProgress", "Upload already in progress, please wait."));
        return;
      }
      
      // Проверяем состояние сервера перед загрузкой большого файла
      if (file.size > 1024 * 1024 * 1024) { // > 1 GB
        setStatusText(t("checkingServerSpace", "Checking server disk space..."));
        try {
          const health = await checkServerHealth();
          const freeSpaceGB = health.system.disk.free_gb || 0;
          const freePercent = health.system.disk.free_percent || 0;
          const requiredSpaceGB = file.size * 1.5 / (1024 * 1024 * 1024);
          
          // Обновляем информацию о сервере
          setServerInfo(health);
          
          // Если свободного места меньше, чем нужно для файла * 1.5
          if (freeSpaceGB < requiredSpaceGB) {
            setError(
              t("notEnoughServerSpace", 
                `Not enough space on server. Required: ${requiredSpaceGB.toFixed(1)} GB, Available: ${freeSpaceGB.toFixed(1)} GB.`)
            );
            return;
          }
          
          // Если свободного места меньше 20%
          if (freePercent < 20) {
            setUploadWarning(
              t("lowServerDiskSpace", 
                `Warning: Server has only ${freePercent.toFixed(1)}% free space. Upload might fail.`)
            );
          }
        } catch (err) {
          console.error("Error checking server health:", err);
          // Продолжаем загрузку, но выдаем предупреждение
          setUploadWarning(t("serverCheckFailed", "Could not verify server space. Upload may fail."));
        }
      }
      
      uploadInProgress.current = true;
      setStatusText(t("startingUpload", "Starting upload..."));
      setProgress(0);
      setUploadProgress(0);
      
      const res = await uploadVideo(file, name, description, (progressEvent) => {
        // Обработка прогресса загрузки
        const percentCompleted = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        setUploadProgress(percentCompleted);
        setStatusText(t("uploadingProgress", `Uploading: ${percentCompleted}%`));
      });
      setTaskId(res.task_id);
      setStatusText(t("processingVideo", "Processing video..."));
    } catch (err) {
      console.error("Upload error:", err);
      uploadInProgress.current = false;
      
      // Обработка специфичных ошибок
      if (err.response?.status === 507) {
        setError(t("noSpaceLeft", "Server disk space is full. Please try again later or contact administrator."));
      } else if (err.response?.status === 413) {
        setError(t("fileTooLarge", "File size is too large for server to process."));
      } else {
        setError(err.response?.data?.detail || err.message || t("uploadFailed", "Upload failed."));
      }
    }
  };

  useEffect(() => {
    let interval;
    if (taskId) {
      interval = setInterval(async () => {
        try {
          const statusRes = await getTaskStatus(taskId);
          setProgress(statusRes.progress || 0);
          setStatusText(statusRes.current_operation || "");
          
          if (statusRes.status === "completed") {
            clearInterval(interval);
            uploadInProgress.current = false;
            // Обновляем информацию о сервере после успешной загрузки
            checkServerStatus();
          } else if (statusRes.status === "failed") {
            clearInterval(interval);
            uploadInProgress.current = false;
            setError(`${t("processingFailed", "Processing failed")}: ${statusRes.error || ''}`);
          }
        } catch (err) {
          console.error("Status check error:", err);
          clearInterval(interval);
          uploadInProgress.current = false;
          setError(err.response?.data?.detail || err.message || t("statusCheckFailed", "Failed to check upload status."));
        }
      }, 2000); // Проверка каждые 2 секунды
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [taskId, t]);

  const handleFileChange = (e) => {
    if (e.target.files.length > 0) {
      const selectedFile = e.target.files[0];
      setFile(selectedFile);
      
      // Отображаем предупреждение, если файл большой
      if (selectedFile.size > 1024 * 1024 * 1024) { // Более 1 ГБ
        setUploadWarning(
          t("largeFileWarning", "You're uploading a large file. It might take a while to process.")
        );
      } else {
        setUploadWarning("");
      }
    }
  };

  // Обработчики для drag & drop
  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFile = e.dataTransfer.files[0];
      setFile(droppedFile);
      
      // Отображаем предупреждение, если файл большой
      if (droppedFile.size > 1024 * 1024 * 1024) { // Более 1 ГБ
        setUploadWarning(
          t("largeFileWarning", "You're uploading a large file. It might take a while to process.")
        );
      } else {
        setUploadWarning("");
      }
      
      e.dataTransfer.clearData();
    }
  };
  
  const getServerStatusColor = () => {
    if (!serverInfo) return "default";
    if (serverInfo.status === "ok") return "success";
    if (serverInfo.status === "warning") return "warning";
    return "error";
  };
  
  const getServerStatusIcon = () => {
    if (!serverInfo) return null;
    if (serverInfo.status === "ok") return <CheckIcon fontSize="small" />;
    if (serverInfo.status === "warning") return <WarningIcon fontSize="small" />;
    return <ErrorIcon fontSize="small" />;
  };

  return (
    <Box>
      {/* Информация о состоянии сервера */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <Tooltip title={t("refreshServerStatus", "Refresh server status")}>
              <IconButton onClick={checkServerStatus} disabled={checkingServer}>
                <StorageIcon />
              </IconButton>
            </Tooltip>
          </Grid>
          <Grid item xs>
            {serverInfo ? (
              <>
                <Typography variant="body2">
                  {t("serverStatus", "Server Status")}:{" "}
                  <Chip 
                    size="small" 
                    color={getServerStatusColor()} 
                    icon={getServerStatusIcon()} 
                    label={serverInfo.status.toUpperCase()} 
                  />
                </Typography>
                <Typography variant="body2">
                  {t("diskSpace", "Free disk space")}:{" "}
                  {formatFileSize(serverInfo.system.disk.free)} ({serverInfo.system.disk.free_percent.toFixed(1)}%)
                </Typography>
                {serverInfo.temp_files && (
                  <Typography variant="body2">
                    {t("tempFiles", "Temp files")}:{" "}
                    {serverInfo.temp_files.count} ({formatFileSize(serverInfo.temp_files.total_size_mb * 1024 * 1024)})
                  </Typography>
                )}
              </>
            ) : (
              <Typography variant="body2">
                {checkingServer ? t("checkingServer", "Checking server status...") : t("serverStatusUnknown", "Server status unknown")}
              </Typography>
            )}
          </Grid>
          <Grid item>
            <Tooltip title={t("cleanupServerFiles", "Clean up temporary files")}>
              <IconButton 
                onClick={handleCleanupTempFiles} 
                disabled={cleaning || !serverInfo}
                color="primary"
              >
                <DeleteSweepIcon />
              </IconButton>
            </Tooltip>
          </Grid>
        </Grid>
      </Box>
      
      <Divider sx={{ mb: 3 }} />
      
      <Box
        component="form"
        onSubmit={handleUpload}
        sx={{
          display: "flex",
          flexDirection: "column",
          gap: 2
        }}
      >
        {/* Область drag & drop / выбора файла */}
        <Paper
          variant="outlined"
          sx={{
            p: 2,
            textAlign: "center",
            borderColor: dragOver ? "primary.main" : "grey.400",
            backgroundColor: dragOver ? "grey.100" : "inherit",
            cursor: "pointer",
            transition: "border-color 0.3s, background-color 0.3s"
          }}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current.click()}
        >
          <Typography variant="body1">
            {file
              ? `${file.name} (${formatFileSize(file.size)})`
              : t("selectFile") ||
                "Select Video File (click or drag & drop)"}
          </Typography>
          <input
            ref={fileInputRef}
            type="file"
            hidden
            accept="video/*"
            onChange={handleFileChange}
          />
        </Paper>
        
        {/* Предупреждение о большом файле */}
        {uploadWarning && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            {uploadWarning}
          </Alert>
        )}
        
        <TextField
          label={t("videoName")}
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
        />
        <TextField
          label={t("description")}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          multiline
          rows={3}
        />
        <Button 
          variant="contained" 
          type="submit"
          disabled={uploadInProgress.current || !file || !name || cleaning}
        >
          {t("uploadVideo")}
        </Button>
      </Box>
      
      {/* Прогресс загрузки файла */}
      {uploadInProgress.current && uploadProgress > 0 && uploadProgress < 100 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            {t("uploadingFile", "Uploading file to server")}
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={uploadProgress} 
            sx={{
              height: 8,
              borderRadius: 4,
              backgroundColor: 'rgba(0, 0, 0, 0.1)',
              '& .MuiLinearProgress-bar': {
                borderRadius: 4,
                backgroundColor: 'primary.main',
              }
            }}
          />
          <Typography variant="caption" sx={{ mt: 0.5, display: 'block' }}>
            {uploadProgress}%
          </Typography>
        </Box>
      )}
      
      {/* Прогресс обработки видео */}
      {(taskId || (uploadInProgress.current && uploadProgress === 100)) && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            {t("processingVideo", "Processing video")}
          </Typography>
          <LinearProgress 
            variant="determinate" 
            value={progress} 
            sx={{
              height: 10,
              borderRadius: 5,
              backgroundColor: 'rgba(0, 0, 0, 0.1)',
              '& .MuiLinearProgress-bar': {
                borderRadius: 5,
                backgroundColor: 'success.main',
              }
            }}
          />
          <Typography variant="body2" sx={{ mt: 1 }}>
            {t("status")}: {statusText} ({progress}%)
          </Typography>
        </Box>
      )}
      
      <AlertMessage
        open={!!error}
        onClose={() => setError("")}
        severity="error"
        message={error}
      />
    </Box>
  );
};

export default VideoUploadForm;
