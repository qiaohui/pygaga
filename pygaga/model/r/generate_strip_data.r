data<-NULL;
features <- c("result", as.vector(as.matrix(read.table("{{features}}", header=TRUE))));
{% for file in files -%}
tmp_data <- read.table("{{file}}", header=TRUE);
tmp_data <- tmp_data[, names(tmp_data) %in% features]
data <- rbind(data, tmp_data);
g<-gc();
{% endfor -%}
write.table(data, file="{{strip_data_file}}")
