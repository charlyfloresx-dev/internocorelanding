using System.ComponentModel.DataAnnotations;
namespace Interno.Domain.Catalog
{
    public class TimeClock
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [MaxLength(45)]
        public string Code { get; set; }
        [StringLength(16, ErrorMessage = "Enter Valid IP."), RegularExpression(@"^([\d]{1,3}\.){3}[\d]{1,3}$")]
        public string IP { get; set; }
        public int Port { get; set; }
        public string Username { get; set; }
        public string Password { get; set; }
    }
}