data <- NULL;
{% for f in column_filenames -%}
data <- rbind(data, read.table("{{f}}", header=TRUE));g<-gc();
{% endfor -%}
x<-c()
n<-names(data)
data$result <- round(data$result, digits=1)
for (name in n) {
   if (name == "result") {
     next
   }
   fmla <- as.formula(paste("result ~ ", name))
   lm.sol<-glm(fmla,data,family={{family}}(), weights=rep(10, dim(data)[1]))
   if (is.null(summary(lm.sol)$coefficients[8])) {
     x[name] <- 1
   } else {
     x[name] <- summary(lm.sol)$coefficients[8]
   }
   if (is.na(x[name])) {
     x[name] <- 1
   }
}
delete <- names(x[x > 0.5])
x <- x[!(names(x) %in% delete)]
write.table(x, file="{{feature_file}}")
