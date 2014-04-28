load("{{glm_model_file}}")
load("{{comp_file}}")
x<-data.frame(pr$loadings[,])
beta<-coef(lm.sol)
gamma<-beta[2:length(beta)]
dim(gamma) <- c(1,length(gamma))
x <- x[, names(x) %in% names(beta)]
m <- gamma%*%t(x)
r <- c(beta[1], m[,])
write.table(r, file = "{{output_file}}")
