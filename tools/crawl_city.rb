require 'rubygems'
require 'spidr'
require 'json'

#Spidr.start_at('http://tq.123cha.com/110000.html',
#    :hosts => ['tq.123cha.com',]) do |spider|
Spidr.host('tq.123cha.com') do |spider|

  spider.user_agent = "Mozilla/4.0 (Windows; MSIE 7.0; Windows NT 5.1; SV1; .NET CLR 2.0.50727)"

  spider.every_html_page do |page|
    #puts "city: #{page.url}"

    tables = page.search('//table')
    if tables.length == 4 then
      id = page.url.path.scan(/(\d+)\.html/).last.first
      name = page.search('//strong')[2].text.sub("相关城市信息", "")
      info = Hash[*(tables[2].search("tr/td").map{|cell| cell.text})].reject{|k,v| k.include?("今天日")}
      result = {name => [id, info]}
      puts "#{result.to_json}"
      $stdout.flush
    end

  end
end
