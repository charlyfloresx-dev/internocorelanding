using Oracle.EntityFrameworkCore;
using System.Collections.Generic;
using Microsoft.EntityFrameworkCore;

namespace OracleBlog
{
	class Program
	{
		public class BloggingContext : DbContext
		{
			public DbSet<Blog> Blogs { get; set; }
			public DbSet<Post> Posts { get; set; }
			protected override void OnConfiguring(DbContextOptionsBuilder optionsBuilder)
			{
				optionsBuilder.UseOracle(@"User Id=blog;Password=<password>;Data Source=pdborcl;");
			}
		}

		public class Blog
		{
			public int BlogId { get; set; }
			public string Url { get; set; }
			public List<Post> Posts { get; set; }
		}

		public class Post
		{
			public int PostId { get; set; }
			public string Title { get; set; }
			public string Content { get; set; }
			public int BlogId { get; set; }
			public Blog Blog { get; set; }
		}

		// static void Main(string[] args)
		// {
		// 	using (var db = new BloggingContext())
		// 	{
		// 		var blog = new Blog { Url = "https://blogs.example.com" };
		// 		db.Blogs.Add(blog);
		// 		db.SaveChanges();
		// 	}
		// 	using (var db = new BloggingContext())
		// 	{
		// 		var blogs = db.Blogs;
		// 	}
		// }
	}
}