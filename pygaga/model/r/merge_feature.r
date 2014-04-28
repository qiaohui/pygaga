data <- NULL;
{% for i in column_blocks -%}
data <- rbind(data, read.table("{{feature_files[i]}}", header=TRUE));
{% endfor -%}
y <- t(data)
names(y) <- row.names(data)
n <- names(y[rank(y) < 400])
write.table(n, file="{{select_feature_file}}")