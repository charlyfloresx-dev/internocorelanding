using System.ComponentModel.DataAnnotations;

namespace Interno.Domain.Catalog
{
    public class Mail
    {
        [Key]
        public int Id { get; set; }
        [Required]
        [DataType(DataType.EmailAddress)]
        public string Email { get; set; }
    }
}