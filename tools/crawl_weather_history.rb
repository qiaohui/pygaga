require 'rubygems'
require 'spidr'
require 'json'
require 'iconv'
require 'ruby-debug'

#Spidr.start_at('http://history.tianqizx.cn/his_741.aspx',
Spidr.start_at('http://history.tianqizx.cn/',
    :hosts => ['history.tianqizx.cn','']) do |spider|

  spider.user_agent = "Mozilla/4.0 (Windows; MSIE 7.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)"

  spider.every_html_page do |page|
    #puts "url: #{page.url}"

    m = page.url.path.match(/his_(\d+)_(\d+)-(\d+)-(\d+)\.aspx/)
    if m then
      #puts "landing page #{m[2..4].to_json}"

      title = page.search("//h1")[0].text
      city = title[0..title.index(m[2])-1]
      weather = page.search("//tr[@id='tr_1']/td")[0].inner_html.gsub(/<br>/, " ").gsub(/<img .*/, "")
      date = "%04d-%02d-%02d" % [m[2], m[3], m[4]]
      gb_w = Iconv.iconv('utf-8', 'gbk', weather)[0].strip
      result = {city => [date, gb_w.split()]}
      puts result.to_json
      $stdout.flush
    end

  end
end
